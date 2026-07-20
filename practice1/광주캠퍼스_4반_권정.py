# -*- coding: utf-8 -*-
"""
=============================================================================
[실습 1] 자료구조 집계 · 컴프리헨션 · 제너레이터
=============================================================================
프로그램 설명
    Sales(거래) 데이터(JSON)를 읽어 다음을 수행하는 데이터 집계 스크립트.
      1) 컴프리헨션 : 고액 거래 필터 + 지역별 총매출 dict 계산
      2) Counter/defaultdict : 지역별 거래 건수, 카테고리별 금액 리스트
      3) 제너레이터 : 고액 거래 스트리밍 + list 대비 메모리 비교
      4) 종합 : 월(month)·카테고리(category)별 총매출 집계

데이터
    Python_Practice1_Data.json 은 로딩 시 파싱 에러가 발생하여,
    로더가 이를 감지하면 Python_Practice2_Data.json 으로 자동 폴백한다.
    (두 파일 모두 동일 스키마: region, category, amount, month)

제출
    광주캠퍼스_4반_권정.py

변경 내역 (Changelog)
    v1.0 (2026-07-20) 최초 작성 - 실습1 요구사항 1~4 및 체크포인트 구현
=============================================================================
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# 로딩 우선순위: 1번 파일 → (에러 시) 2번 파일 폴백
DATA_CANDIDATES = ["Python_Practice1_Data.json", "Python_Practice2_Data.json"]
HIGH_VALUE_THRESHOLD = 1000  # 고액 거래 기준 금액


# ---------------------------------------------------------------------------
# 데이터 로딩 : 파일 부재 / JSON 파싱 오류를 처리하고 정상 파일로 폴백
# ---------------------------------------------------------------------------
def load_sales_data(candidates: list[str]) -> list[dict]:
    """후보 파일들을 순서대로 시도해 처음으로 성공한 JSON(list)을 반환한다.

    - FileNotFoundError : 파일이 없으면 다음 후보로 넘어간다.
    - JSONDecodeError    : 파싱 실패 시(1번 파일 케이스) 다음 후보로 넘어간다.
    - 모든 후보 실패 시    : RuntimeError 로 상위에 전파한다.
    """
    for name in candidates:
        path = Path(name)
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"[WARN] 파일 없음 → 건너뜀: {name}")
            continue
        except json.JSONDecodeError as e:
            print(f"[WARN] JSON 파싱 실패 → 건너뜀: {name} ({e})")
            continue
        else:
            if not isinstance(data, list) or not data:
                print(f"[WARN] 빈 데이터/형식 불일치 → 건너뜀: {name}")
                continue
            print(f"[INFO] 로딩 성공: {name} (총 {len(data)}건)")
            return data
        finally:
            print(f"[INFO] 로딩 시도 완료: {name}")

    raise RuntimeError("사용 가능한 데이터 파일이 없습니다.")


# ---------------------------------------------------------------------------
# 1) 리스트 / 딕셔너리 컴프리헨션
# ---------------------------------------------------------------------------
def filter_high_value(sales: list[dict], threshold: int = HIGH_VALUE_THRESHOLD) -> list[dict]:
    """amount >= threshold 인 거래만 필터링 (리스트 컴프리헨션)."""
    return [row for row in sales if row.get("amount", 0) >= threshold]


def region_total_sales(sales: list[dict]) -> dict[str, int]:
    """지역별 총매출 dict 를 딕셔너리 컴프리헨션으로 계산.

    for 루프 누적 대신, 고유 지역 집합을 순회하는 컴프리헨션으로 합산한다.
    """
    regions = {row["region"] for row in sales}  # 집합 컴프리헨션 (중복 제거)
    return {
        region: sum(row["amount"] for row in sales if row["region"] == region)
        for region in regions
    }


# ---------------------------------------------------------------------------
# 2) Counter + defaultdict
# ---------------------------------------------------------------------------
def count_by_region(sales: list[dict]) -> Counter:
    """지역별 거래 '건수' 를 Counter 로 집계 (직접 루프 카운팅 금지)."""
    return Counter(row["region"] for row in sales)


def amounts_by_category(sales: list[dict]) -> defaultdict:
    """카테고리별 amount 리스트를 defaultdict(list) 로 그룹핑.

    'if key not in dict' 패턴 대신 defaultdict 로 키 자동 생성.
    """
    grouped: defaultdict = defaultdict(list)
    for row in sales:
        grouped[row["category"]].append(row["amount"])
    return grouped


# ---------------------------------------------------------------------------
# 3) 제너레이터 + 메모리 비교
# ---------------------------------------------------------------------------
def gen_high_value(sales: list[dict], threshold: int = HIGH_VALUE_THRESHOLD):
    """amount > threshold 인 거래만 하나씩 yield 하는 제너레이터."""
    for row in sales:
        if row.get("amount", 0) > threshold:
            yield row


def compare_memory(sales: list[dict], threshold: int = HIGH_VALUE_THRESHOLD) -> tuple[int, int]:
    """제너레이터 객체와 list 의 메모리 크기를 비교해 (gen_size, list_size) 반환.

    주의: 측정 대상 제너레이터를 list 로 변환하지 않는다.
    list 는 별도 컴프리헨션으로 독립 생성하여 공정하게 비교한다.
    """
    gen_obj = gen_high_value(sales, threshold)                      # 미소비 제너레이터
    list_obj = [row for row in sales if row.get("amount", 0) > threshold]
    return sys.getsizeof(gen_obj), sys.getsizeof(list_obj)


# ---------------------------------------------------------------------------
# 4) 종합 : 월 · 카테고리별 총매출 집계
# ---------------------------------------------------------------------------
def monthly_category_sales(sales: list[dict]) -> dict[str, int]:
    """(month, category) 조합별 총매출을 defaultdict 로 누적한 뒤
    'YYYY-MM|카테고리' 키의 dict 로 정리(딕셔너리 컴프리헨션)한다."""
    totals: defaultdict = defaultdict(int)
    for row in sales:
        totals[(row["month"], row["category"])] += row["amount"]
    # 정렬 + 사람이 읽기 좋은 키로 변환 (컴프리헨션)
    return {
        f"{month}|{category}": amount
        for (month, category), amount in sorted(totals.items())
    }


# ---------------------------------------------------------------------------
# 실행 엔트리포인트
# ---------------------------------------------------------------------------
def main() -> None:
    try:
        sales = load_sales_data(DATA_CANDIDATES)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    # --- 1) 컴프리헨션 ------------------------------------------------------
    high = filter_high_value(sales)
    region_total = region_total_sales(sales)
    print("\n[1] 컴프리헨션")
    print(f"  amount>={HIGH_VALUE_THRESHOLD} 거래: {len(high)}건")
    print(f"  지역별 총매출: {region_total}")

    # 체크포인트: region_total 값 정확성 검증
    #   defaultdict 로 독립 재계산한 결과와 컴프리헨션 결과가 일치하는지 교차검증
    ref_total: defaultdict = defaultdict(int)
    for r in sales:
        ref_total[r["region"]] += r["amount"]
    assert region_total == dict(ref_total), "지역별 총매출 불일치"
    assert all(v >= 0 for v in region_total.values()), "음수 매출 존재"

    # 체크포인트: top3 지역(총매출) 내림차순 정렬
    top3 = sorted(region_total.items(), key=lambda kv: kv[1], reverse=True)[:3]
    assert [v for _, v in top3] == sorted((v for _, v in top3), reverse=True), "top3 정렬 오류"
    print(f"  top3 지역(총매출↓): {top3}")

    # --- 2) Counter + defaultdict -----------------------------------------
    region_count = count_by_region(sales)
    cat_amounts = amounts_by_category(sales)
    print("\n[2] Counter + defaultdict")
    print(f"  지역별 거래건수 most_common(3): {region_count.most_common(3)}")
    print(f"  카테고리별 건수: { {c: len(v) for c, v in cat_amounts.items()} }")

    # --- 3) 제너레이터 메모리 비교 ----------------------------------------
    gen_size, list_size = compare_memory(sales)
    print("\n[3] 제너레이터 vs list 메모리")
    print(f"  generator: {gen_size} bytes / list: {list_size} bytes")
    assert gen_size < list_size, "제너레이터가 list보다 작아야 함"

    # --- 4) 월·카테고리 매출 집계 -----------------------------------------
    mc_sales = monthly_category_sales(sales)
    print("\n[4] 월·카테고리별 총매출")
    for key, amount in mc_sales.items():
        print(f"  {key}: {amount}")

    # 체크포인트: top3 금액 내림차순 정렬 (종합 집계 기준)
    top3_mc = sorted(mc_sales.items(), key=lambda kv: kv[1], reverse=True)[:3]
    assert [v for _, v in top3_mc] == sorted((v for _, v in top3_mc), reverse=True), "top3 정렬 오류"
    print(f"  top3(월·카테고리 금액↓): {top3_mc}")

    print("\n[OK] 모든 체크포인트 통과")


if __name__ == "__main__":
    main()
