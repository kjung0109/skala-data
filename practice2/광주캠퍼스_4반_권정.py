# -*- coding: utf-8 -*-
"""
=============================================================================
[실습 2] 파일 I/O · 예외 처리 · Pydantic v2 검증 파이프라인
=============================================================================
프로그램 설명
    Sales(거래) 원본 데이터를 읽어 Pydantic v2 로 검증하고,
    통과분(valid)/실패분(errors)을 분리하여 저장·재로딩까지 수행한다.

    파이프라인 : load_raw → validate → save(CSV/JSON) → reload(CSV)
      1) safe_load_csv() : 예외 처리 기반 안전한 CSV 로더
      2) SalesRecord      : month·region 필수, amount>0, category 선택
      3) validate_records : valid / errors({row, error}) 분리
      4) 저장 + 재로딩     : valid→CSV, errors→JSON, 재로딩 건수 검증

데이터
    스펙 지정 원본 Python_Practice1_Data.json 은 표준 JSON 이 아니라
    `sales = [...]` 형태이므로, 로더가 JSON 파싱 실패 시 Python 리터럴로 폴백한다.
    또한 원본은 모두 정상 데이터라 검증 실패가 없으므로, valid/errors 분리와
    ValidationError 출력을 시연하기 위해 DIRTY_SAMPLES 를 원본 뒤에 덧붙인다.

제출
    광주캠퍼스_4반_권정.py

변경 내역 (Changelog)
    v1.0 (2026-07-20) 최초 작성 - 실습2 요구사항 1~4 및 체크포인트 구현
=============================================================================
"""

import ast
import csv
import json
import logging
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("practice2")

BASE = Path(__file__).resolve().parent
SOURCE_JSON = "Python_Practice1_Data.json"   # 스펙 지정 원본 (JSON 아닌 'sales=[...]' 형태)
VALID_CSV = BASE / "valid_records.csv"        # 검증 통과분 저장 경로
ERRORS_JSON = BASE / "errors.json"            # 검증 실패분 저장 경로

# 검증 실패 시연용 불량 레코드 (실데이터는 모두 정상이므로 의도적으로 추가)
DIRTY_SAMPLES = [
    {"region": "", "category": "전자", "amount": 1000, "month": "2024-01"},    # region 빈값
    {"region": "서울", "category": "의류", "amount": -50, "month": "2024-02"},  # amount<=0
    {"region": "부산", "category": "식품", "amount": 500, "month": ""},         # month 빈값
]


class SalesRecord(BaseModel):
    """Sales 레코드 스키마: month·region 필수, amount 양수, category 선택."""

    month: str = Field(min_length=1)
    region: str = Field(min_length=1)
    amount: float = Field(gt=0)
    category: str | None = None


def find_data_file(name: str) -> Path | None:
    """스크립트 폴더 → 상위 폴더 순으로 데이터 파일을 탐색한다."""
    return next((d / name for d in (BASE, BASE.parent) if (d / name).exists()), None)


def load_raw_data(name: str) -> list[dict]:
    """원본 Sales 데이터를 로드한다.

    - 1차: 표준 JSON 파싱 시도
    - 2차: JSON 이 아니면(`sales = [...]` 형태) '[' 부터 Python 리터럴로 안전 파싱
    - 실패/부재 시: logger.error 후 빈 리스트 반환
    """
    path = find_data_file(name)
    if path is None:
        logger.error("원본 데이터 없음: %s", name)
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        logger.error("원본 읽기 실패: %s (%s)", name, e)
        return []
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("JSON 파싱 실패 → Python 리터럴로 재시도: %s", name)
        try:
            return ast.literal_eval(text[text.index("["):])
        except (ValueError, SyntaxError) as e:
            logger.error("원본 파싱 실패: %s (%s)", name, e)
            return []


def validate_records(raw: list[dict]) -> tuple[list[SalesRecord], list[dict]]:
    """raw 를 SalesRecord 로 검증해 (valid, errors) 로 분리한다."""
    valid: list[SalesRecord] = []
    errors: list[dict] = []
    for i, row in enumerate(raw):
        try:
            valid.append(SalesRecord(**row))
        except ValidationError as e:
            errors.append({"row": i, "error": str(e)})
    return valid, errors


def save_valid_csv(records: list[SalesRecord], path: Path) -> None:
    """valid 레코드를 CSV 로 저장한다 (model_dump 사용)."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(SalesRecord.model_fields))
        writer.writeheader()
        writer.writerows(r.model_dump() for r in records)


def save_errors_json(errors: list[dict], path: Path) -> None:
    """errors 를 JSON 으로 저장한다 (ensure_ascii=False 로 한글 보존)."""
    path.write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_load_csv(path: str | Path) -> list[dict] | None:
    """CSV 를 안전하게 로드한다.

    - 파일 없음 : logger.error 후 None 반환
    - 성공      : logger.info 후 dict 리스트 반환
    - 공통      : finally 에서 '로딩 종료' 출력
    """
    try:
        with open(path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        logger.error("파일 없음: %s", path)
        return None
    else:
        logger.info("로딩 성공: %s (%d건)", path, len(rows))
        return rows
    finally:
        logger.info("로딩 종료")


def report_errors(errors: list[dict]) -> None:
    """검증 실패 내역(어느 행이 왜 실패했는지)을 출력한다."""
    for e in errors:
        print(f"\n[ValidationError] row={e['row']}\n{e['error']}")


def main() -> None:
    raw = load_raw_data(SOURCE_JSON) + DIRTY_SAMPLES     # 원본 + 시연용 불량 레코드
    valid, errors = validate_records(raw)                # 검증 → valid/errors 분리
    logger.info("검증 결과 — valid: %d건 / errors: %d건", len(valid), len(errors))
    report_errors(errors)

    save_valid_csv(valid, VALID_CSV)                     # valid → CSV
    save_errors_json(errors, ERRORS_JSON)                # errors → JSON

    reloaded = safe_load_csv(VALID_CSV)                  # 재로딩 후 건수 검증
    assert reloaded is not None and len(reloaded) == len(valid), "재로딩 건수 불일치"
    assert safe_load_csv(BASE / "no_such_file.csv") is None, "None 반환 실패"

    print(f"\n[OK] valid {len(valid)}건 저장·재로딩 확인 / errors {len(errors)}건 기록 완료")


if __name__ == "__main__":
    main()
