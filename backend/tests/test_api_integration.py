import io

from fastapi.testclient import TestClient
from openpyxl import Workbook, load_workbook

from backend.app import main


def sample_xlsx(rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["코너명", "도로명주소"])
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_upload_preview():
    client = TestClient(main.app)
    response = client.post("/api/columns", files={
        "file": ("sample.xlsx", sample_xlsx([["A", "서울 종로구 세종대로 209"]]),
                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    })
    assert response.status_code == 200
    assert response.json()["columns"] == ["코너명", "도로명주소"]
    assert response.json()["row_count"] == 1


def test_convert_preserves_source_and_adds_api_columns(monkeypatch):
    monkeypatch.setenv("JUSO_API_KEY", "test-only-key")

    async def fake_search(self, keyword, page=1, count=20):
        return {"total": 1, "candidates": [{
            "roadAddrPart1": "서울특별시 종로구 세종대로 209",
            "jibunAddr": "서울특별시 종로구 세종로 1-57",
            "engAddr": "209, Sejong-daero, Jongno-gu, Seoul"
        }]}

    monkeypatch.setattr(main.JusoClient, "search", fake_search)
    client = TestClient(main.app)
    response = client.post("/api/convert",
        data={"address_column": "도로명주소"},
        files={"file": ("sample.xlsx", sample_xlsx([["A", "서울 종로구 세종대로 209"]]),
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert response.status_code == 200
    book = load_workbook(io.BytesIO(response.content), read_only=True)
    rows = list(book.active.values)
    assert rows[0] == ("코너명", "도로명주소", "API_도로명주소", "API_지번주소", "API_영문주소", "주소검증상태")
    assert rows[1][0] == "A"
    assert rows[1][-1] == "MATCHED_SINGLE"
    book.close()


def test_convert_ambiguous_keeps_api_fields_empty(monkeypatch):
    monkeypatch.setenv("JUSO_API_KEY", "test-only-key")

    async def fake_search(self, keyword, page=1, count=20):
        return {"total": 2, "candidates": [{"roadAddrPart1": "A"}, {"roadAddrPart1": "B"}]}

    monkeypatch.setattr(main.JusoClient, "search", fake_search)
    response = TestClient(main.app).post("/api/convert",
        data={"address_column": "도로명주소"},
        files={"file": ("sample.xlsx", sample_xlsx([["A", "서울 종로구 세종대로 209"]]),
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert response.status_code == 200
    book = load_workbook(io.BytesIO(response.content), read_only=True)
    row = list(book.active.values)[1]
    assert row[-1] == "REVIEW_MULTIPLE"
    assert row[-4:-1] == (None, None, None)
    book.close()
