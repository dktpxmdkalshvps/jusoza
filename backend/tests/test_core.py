from io import BytesIO
from openpyxl import Workbook, load_workbook
from app.excel import parse_excel, export_excel
from app.matching import match_address

def test_3000_rows_preserved():
    wb = Workbook()
    ws = wb.active
    ws.append(["코너명", "지번주소", "도로명주소"])
    for i in range(3000):
        ws.append([f"코너{i}", f"지번{i}", ""])
    buf = BytesIO()
    wb.save(buf)
    source = buf.getvalue()
    rows = parse_excel(source, "지번주소", "도로명주소")
    assert len(rows) == 3000
    output = load_workbook(BytesIO(export_excel(source, {})))
    assert output.active.max_row == 3001
    assert output.active["A3001"].value == "코너2999"

def test_ambiguous_candidate_not_auto_approved():
    result = match_address({"candidates": [{"bdMgtSn": "1", "roadAddrPart1": "A"}]}, None)
    assert result["status"] == "REVIEW_REQUIRED"

def test_same_building_can_be_verified():
    candidate = {"bdMgtSn": "123", "roadAddrPart1": "서울 테스트로 1"}
    result = match_address({"candidates": [candidate]}, {"candidates": [candidate]})
    assert result["status"] == "VERIFIED"
