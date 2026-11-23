def match_address(jibun_result: dict | None, road_result: dict | None) -> dict:
    """Conservative matcher: never silently choose the first ambiguous candidate."""
    a = (jibun_result or {}).get("candidates", [])
    b = (road_result or {}).get("candidates", [])
    if a and b:
        a_ids = {x.get("bdMgtSn") for x in a if x.get("bdMgtSn")}
        b_ids = {x.get("bdMgtSn") for x in b if x.get("bdMgtSn")}
        shared = a_ids & b_ids
        if len(shared) == 1:
            matches = [x for x in a + b if x.get("bdMgtSn") in shared]
            roads = {x.get("roadAddrPart1") for x in matches}
            if len(roads) == 1 and next(iter(roads)):
                candidate = matches[0]
                return {"status": "VERIFIED", "road_address": candidate["roadAddrPart1"],
                        "building_id": candidate["bdMgtSn"]}
    return {"status": "REVIEW_REQUIRED" if a or b else "NOT_FOUND",
            "road_address": None, "building_id": None}
