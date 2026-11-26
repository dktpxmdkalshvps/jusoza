import csv
import io
import os
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openpyxl import Workbook, load_workbook

from backend.app.juso import JusoClient

app = FastAPI(title="Jusoza", version="0.2.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "").split(",") if x.strip()]
if origins:
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["*"])

MAX_BYTES = 3 * 1024 * 1024
MAX_ROWS = 30  # synchronous MVP safety limit; background jobs required for 3,000+
OUTPUT_FIELDS = ["API_도로명주소", "API_지번주소", "API_영문주소", "주소검증상태"]

@app.get("/health")
def health():
    return {"ok": True, "service": "jusoza"}

def read_rows(data: bytes, filename: str):
    suffix = Path(filename).suffix.lower()
    if suffix == ".xlsx":
        try:
            book = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            try:
                sheet = book.active
                rows = list(sheet.iter_rows(values_only=True))
            finally:
                book.close()
        except Exception as exc:
            raise HTTPException(400, "유효한 XLSX 파일이 아닙니다.") from exc
    elif suffix == ".csv":
        try:
            decoded = data.decode("utf-8-sig")
            rows = list(csv.reader(io.StringIO(decoded)))
        except UnicodeDecodeError as exc:
            raise HTTPException(400, "CSV는 UTF-8 인코딩이어야 합니다.") from exc
    else:
        raise HTTPException(400, "XLSX 또는 CSV 파일만 지원합니다.")
    if not rows:
        raise HTTPException(400, "파일이 비어 있습니다.")
    headers = [str(x).strip() if x is not None else "" for x in rows[0]]
    if not any(headers) or len(headers) != len(set(headers)):
        raise HTTPException(400, "첫 행의 컬럼명이 비어 있거나 중복되었습니다.")
    records = [list(row[:len(headers)]) + [None] * max(0, len(headers)-len(row)) for row in rows[1:]]
    if len(records) > MAX_ROWS:
        raise HTTPException(413, f"현재 MVP는 최대 {MAX_ROWS}행만 처리합니다.")
    return headers, records

async def get_upload(upload: UploadFile):
    if not upload.filename:
        raise HTTPException(400, "파일 이름이 없습니다.")
    data = await upload.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "파일 크기는 최대 3MB입니다.")
    return read_rows(data, upload.filename)

@app.post("/api/columns")
async def columns(file: UploadFile = File(...)):
    headers, rows = await get_upload(file)
    return {"columns": headers, "row_count": len(rows), "preview": rows[:5], "max_rows": MAX_ROWS}

def pick_candidate(result, query):
    candidates = result["candidates"]
    if not candidates:
        return "NOT_FOUND", None
    if result["total"] == 1 and len(candidates) == 1:
        return "MATCHED_SINGLE", candidates[0]
    # Do not silently choose a result from ambiguous candidates.
    return "REVIEW_MULTIPLE", None

@app.post("/api/convert")
async def convert(file: UploadFile = File(...), address_column: str = Form(...)):
    headers, rows = await get_upload(file)
    if address_column not in headers:
        raise HTTPException(400, "선택한 주소 컬럼이 존재하지 않습니다.")
    if not os.getenv("JUSO_API_KEY"):
        raise HTTPException(503, "서버의 주소 API 승인키가 설정되지 않았습니다.")
    idx = headers.index(address_column)
    output = Workbook()
    sheet = output.active
    sheet.title = "주소변환결과"
    sheet.append(headers + OUTPUT_FIELDS)
    cache = {}
    async_client = JusoClient()
    for row in rows:
        keyword = str(row[idx] or "").strip()
        if not keyword:
            result = ("EMPTY_ADDRESS", None)
        elif keyword in cache:
            result = cache[keyword]
        else:
            try:
                response = await async_client.search(keyword, count=20)
                result = pick_candidate(response, keyword)
            except Exception:
                result = ("API_ERROR", None)
            cache[keyword] = result
        status, candidate = result
        sheet.append(row + [
            candidate.get("roadAddrPart1", "") if candidate else "",
            candidate.get("jibunAddr", "") if candidate else "",
            candidate.get("engAddr", "") if candidate else "",
            status
        ])
    stream = io.BytesIO()
    output.save(stream)
    stream.seek(0)
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="jusoza_result.xlsx"'})
