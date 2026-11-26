import io
from openpyxl import Workbook
from fastapi import HTTPException
from backend.app.main import read_rows, pick_candidate

def test_xlsx_preserves_headers_and_rows():
    wb=Workbook(); ws=wb.active
    ws.append(["이름","도로명주소"]); ws.append(["A","서울시 종로구 세종대로 209"])
    buf=io.BytesIO(); wb.save(buf)
    headers, rows=read_rows(buf.getvalue(),"sample.xlsx")
    assert headers==["이름","도로명주소"]
    assert rows==[["A","서울시 종로구 세종대로 209"]]

def test_ambiguous_candidate_never_auto_selected():
    result={"total":2,"candidates":[{"roadAddrPart1":"A"},{"roadAddrPart1":"B"}]}
    assert pick_candidate(result,"주소")[0]=="REVIEW_MULTIPLE"

def test_single_candidate():
    result={"total":1,"candidates":[{"roadAddrPart1":"A"}]}
    assert pick_candidate(result,"주소")[0]=="MATCHED_SINGLE"

def test_row_limit():
    wb=Workbook(); ws=wb.active; ws.append(["주소"])
    for i in range(31): ws.append([str(i)])
    buf=io.BytesIO(); wb.save(buf)
    try: read_rows(buf.getvalue(),"sample.xlsx")
    except HTTPException as exc: assert exc.status_code==413
    else: assert False, "expected 413"
