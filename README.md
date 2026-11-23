# jusoza

행정안전부 주소정보 검색 API 기반 엑셀 주소 현행화 웹서비스.

## 목표
매번 새로운 XLSX 파일을 업로드하고, 최소 3,000행의 주소를 공식 API로 검증하여 결과 열이 추가된 XLSX 파일을 반환합니다. 원본 행과 순서는 보존하고, 불확실한 후보는 자동 확정하지 않습니다.

## 현재 구현 (초기 스캐폴드)
- FastAPI `GET /health`
- 행안부 주소 검색 비동기 HTTP 클라이언트 기본형
- 지번/도로명 검색 결과의 건물관리번호 교차 비교
- XLSX 읽기 및 공식주소/건물관리번호/검증상태 열 추가
- React + Vite 초기 화면
- 3,000행 보존 및 매칭 로직 단위 테스트 코드

**미구현:** 파일 업로드 API, 영속 작업 큐, 배치 Worker, 진행률 API, 다운로드 API, 인증 및 운영 배포. 실제 행안부 API 연동과 테스트 통과 여부는 아직 확인하지 않았습니다.

## 로컬 실행
Python 3.12+ 권장:

```bash
cd backend
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest -q
```

프론트엔드(Node.js 20+ 권장):

```bash
cd frontend
npm install
npm run dev
npm run build
```

실제 주소 API 호출 전 `JUSO_API_KEY` 환경변수를 서버에 설정하세요. `.env.example`은 설정 항목 참고용이며, 실제 키를 Git에 커밋하지 마세요.

## 다음 구현 순서
1. 공식 API 응답 검증 및 HTTP 오류/429 재시도·속도 제한
2. 업로드 API 및 XLSX 열 매핑·파일 검증
3. PostgreSQL 작업/행 상태와 별도 Worker (중단 복구)
4. 결과 XLSX 다운로드 및 React 진행률 화면
5. Mock 기반 3,000행 E2E, 실제 API 승인키 기반 스모크 테스트

## 참고
- https://openapi-kr.github.io/oas/mois/juso/
- https://business.juso.go.kr/
