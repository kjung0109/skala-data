# [Day1 종합] 데이터 수집 미니 파이프라인

3개 공개 API를 **비동기로 동시 수집** → **Pydantic v2 검증** → **CSV·Parquet 저장 및 성능 비교**하는 미니 데이터 파이프라인.

- 제출: 광주캠퍼스 4반 권정
- 과정: SKALA 2) AI의 서비스화 — 데이터분석 및 AIOps / 1. 데이터 분석을 위한 Python 이해

---

## 📁 폴더 구조

```
practice_day1/
├── models.py         # Pydantic v2 스키마 (타입·범위 검증) + from_api 추출
├── collect.py        # httpx AsyncClient + asyncio.gather 동시 수집 (백오프 재시도)
├── storage.py        # CSV/Parquet 저장 + 읽기/쓰기 성능 측정·비교
├── main.py           # 수집 → 검증 → 저장 → 비교 오케스트레이션
├── test_models.py    # pytest: 스키마·파이프라인·재시도 검증 (8건)
├── requirements.txt  # pip freeze 버전 고정
└── output/           # 실행 산출물 (gitignore, 재생성)
```

## 🔌 수집 대상 API

| 이름 | 내용 | 엔드포인트 |
|---|---|---|
| weather | 서울 3일 시간대별 기온·강수확률 | Open-Meteo |
| country | 한국 국가 정보 | Countries.dev |
| ip | IP(8.8.8.8) 기반 지역 정보 | ip-api |

## ⚙️ 설치 & 실행

```bash
# 1) 가상환경 활성화 후 패키지 설치
source .venv/bin/activate
pip install -r requirements.txt

# 2) 파이프라인 실행
python main.py

# 3) 테스트 & 스타일 검사
pytest -q
ruff check .
```

## 🔄 파이프라인 흐름

```
collect_all()            # ① asyncio.gather 로 3개 API 동시 호출 (실패 시 백오프 재시도)
   → validate_all()      # ② 각 응답을 Pydantic 모델로 타입·범위 검증 (실패분은 예외 처리로 제외)
   → save_and_compare()  # ③ 검증 통과 데이터를 CSV·Parquet 저장 + 읽기/쓰기 시간 측정
   → print_comparison()  # ④ 형식별 성능 비교 출력
```

## 📊 성능 비교 결과 (예시)

| 데이터 | 행 수 | CSV 크기 | Parquet 크기 |
|---|---|---|---|
| weather | 72 | 1.79 KB | 3.01 KB |
| country | 1 | 0.12 KB | 4.27 KB |
| ip | 1 | 0.14 KB | 5.21 KB |

**해석:** 데이터가 작을수록 Parquet의 스키마·푸터 메타데이터 **고정 오버헤드**가 커져 CSV보다 크고 느리다(1행에서 30배 이상). 행 수가 늘수록 격차가 줄며, 대용량·컬럼 선택 조회에서는 Parquet가 역전해 유리해진다. → **소량은 CSV, 대용량은 Parquet.**

## 🧪 테스트 (pytest 8건)

- 3개 모델 정상 파싱 / 타입·범위 위반 시 `ValidationError`·`ValueError`
- `validate_all`: 일부 불량 레코드가 있어도 나머지는 통과하고 크래시하지 않음
- `fetch_json`: 일시적 5xx 오류 시 백오프 재시도 후 성공 (MockTransport, 네트워크 불요)

## 🧩 설계 특징

- **계층 분리**: 수집·검증·저장을 독립 모듈로 분리해 테스트·재사용 용이
- **비동기 동시성**: `asyncio.gather` 로 순차 대비 대기시간 단축, 부분 실패 허용
- **견고성**: 일시적 HTTP 오류 백오프 재시도, 검증 실패 개별 예외 처리
- **타입 안정성**: 전 함수 타입 힌트 + Pydantic 범위 검증
- **재현성**: `requirements.txt` 버전 고정, pytest·ruff 통과
