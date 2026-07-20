# CLAUDE.md — 데이터분석 및 AIOps 실습 프로젝트

SKALA `2) AI의 서비스화 — 데이터분석 및 AIOps` 과정의 Python 실습 저장소.
(강의: "1. 데이터 분석을 위한 Python 이해", 강사 백정열)

---

## 👤 제출자 정보 (제출 파일명에 사용)

- 캠퍼스: **광주캠퍼스**
- 반: **4반**
- 이름: **권정**
- 제출 파일명 규칙: `캠퍼스명_반_이름` → 예) `광주캠퍼스_4반_권정.py`

---

## 🧰 개발 환경

- Python **3.11** (Homebrew), 가상환경 `.venv/`
- 실행은 항상 venv 기준으로:
  ```bash
  cd /Users/jung/data-project
  .venv/bin/python <파일명>.py          # 활성화 없이 바로 실행
  # 또는
  source .venv/bin/activate && python <파일명>.py
  ```
- `.venv/` 는 `.gitignore` 처리, **`requirements.txt` 는 반드시 커밋** (강의 규칙, 18p/53p)
- 패키지 추가 시: `.venv/bin/pip install <pkg>` 후 `.venv/bin/pip freeze > requirements.txt`
  - ⚠️ 실습과 무관하게 설치한 도구는 requirements 에 섞지 말 것 (freeze 전에 정리)

---

## 🌿 Git 워크플로 (사용자 선호)

- **작업 시작 시 브랜치부터 판다.** 기반 브랜치는 `main`.
- 브랜치명 규칙: `practice<N>/<내용>` 예) `practice1/data-structures`, `day1/pipeline`
  ```bash
  git switch -c practice1/data-structures
  ```
- **커밋·머지는 사용자가 직접 한다. Claude 는 메시지와 명령어만 추천한다.** (실행하지 말 것)
- 커밋 메시지: Conventional Commits (`feat:`, `fix:`, `merge:` 등) + 한글 본문 불릿
- 머지는 `--no-ff` 권장 (실습 단위 이력 보존):
  ```bash
  git switch main
  git merge --no-ff practice1/data-structures -m "merge: 실습1 ... 통합"
  ```
- 원격: `skala-data` (GitHub)

---

## 📝 실습 제출 규칙 (중요)

| 구분 | 제출물 |
|---|---|
| **개별 Practice 1~4** | `캠퍼스명_반_이름.py` **단일 .py 파일만** |
| **종합실습 (Day1/Day2)** | `캠퍼스명_반_이름_실습명.zip` (폴더 전체 코드) + 실행결과·의견 **PDF** |

- 납기: 개별 실습은 **1시간 내 제출**. 종합실습은 별도 기한(초과 시 감점).

---

## 📊 채점 기준

### 개별 Practice 1~4 공통 루브릭 (100점)
| 항목 | 배점 | 핵심 |
|---|---|---|
| Code의 Comm. | 20 | **머리말**: 프로그램 전체 설명 + **변경내역(Changelog)** / **중간**: 함수·기능 설명 주석 |
| 코드 간결성 | 35 | 불필요한 반복 지양 (컴프리헨션·내장함수 활용) |
| 오류/예외 처리 | 35 | 간단한 코드라도 **try/except 필수** |
| 납기 | 10 | 1시간 내 제출 |

### 종합실습(Day1) 루브릭 (100점)
환경구성+비동기수집 35 / 스키마검증+저장비교 45 / 테스트·커밋 10 / 완성도(주석) 10

> 실습별 세부 Checkpoint·감점 항목은 강의 PDF 참고. 코드 작성 후 **항상 만점 기준으로 체크포인트/감점 대조**할 것.

---

## 🗂 데이터 파일 주의사항

- `Python_Practice1_Data.json` 은 **JSON 파싱 에러**(빈 값) → 로딩 실패함.
- **`Python_Practice2_Data.json` 사용** (100건, 스키마 동일: `region`, `category`, `amount`, `month`).
- 두 파일 모두 채점자 배포본. `.py` 만 제출해도 채점 환경에 데이터가 있으므로 동작.
- 권장 패턴: 로더가 1번 파일 시도 → `JSONDecodeError` 폴백 → 2번 파일 (예외처리 점수에도 유리).

---

## ✅ 진행 현황

- **실습 1** (`practice1/data-structures`): 완료·머지. `광주캠퍼스_4반_권정.py`
  - 자료구조 집계 · 컴프리헨션 · 제너레이터. 체크포인트 4/4, 감점 0.
- 이후: 실습 2(파일 I/O·예외·Pydantic), Day1 종합(asyncio·httpx 수집 파이프라인), 실습 3~4, Day2 종합.

---

## 🤖 Claude 작업 규칙 요약

1. 작업 시작 → **브랜치 먼저 생성** (Claude 가 생성해도 됨).
2. 코드 작성 후 **체크포인트·감점 기준 자체 검증** + 실제 실행으로 통과 확인.
3. **커밋/머지는 하지 말고** 메시지·명령어만 추천.
4. 제출 파일명·규칙(위) 준수. 개별 실습은 `.py` 하나.
