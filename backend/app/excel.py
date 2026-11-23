from io import BytesIO
from openpyxl import load_workbook

RESULT_COLUMNS = ["공식도로명주소", "건물관리번호", "검증상태"]

def parse_excel(data: bytes, jibun_column: str, road_column: str):
    wb = load_workbook(BytesIO(data), read_only=True, data_only=True)
    try:
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        headers = [str(v).strip() if v is not None else "" for v in next(rows)]
        if jibun_column not in headers or road_column not in headers:
            raise ValueError("Required address columns not found")
        ji, ro = headers.index(jibun_column), headers.index(road_column)
        return [(i, str(row[ji] or "").strip(), str(row[ro] or "").strip())
                for i, row in enumerate(rows, start=2)]
    finally:
        wb.close()

def export_excel(source: bytes, results: dict[int, dict]) -> bytes:
    wb = load_workbook(BytesIO(source))
    ws = wb.active
    first = ws.max_column + 1
    for offset, name in enumerate(RESULT_COLUMNS):
        ws.cell(1, first + offset, name)
    for row_num in range(2, ws.max_row + 1):
        result = results.get(row_num, {})
        for offset, key in enumerate(("road_address", "building_id", "status")):
            ws.cell(row_num, first + offset, result.get(key, ""))
    output = BytesIO()
    wb.save(output)
    return output.getvalue()
