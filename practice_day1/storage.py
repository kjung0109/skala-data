# -*- coding: utf-8 -*-
"""
=============================================================================
[Day1 종합] storage — CSV / Parquet 저장 및 읽기·쓰기 성능 비교
=============================================================================
프로그램 설명
    검증 통과 데이터(DataFrame)를 CSV·Parquet 두 형식으로 저장하고,
    각 형식의 쓰기/읽기 시간과 파일 크기를 측정해 비교한다.
    시간이 매우 짧으므로 repeat 회 반복 측정 후 평균을 사용한다.

함수 구성 (파라미터 · 기능)
    save_both(df, csv_path, parquet_path) -> None
        df 를 CSV·Parquet 두 형식으로 저장 (성능 측정 없이).
    save_and_compare(df, csv_path, parquet_path, repeat=100) -> dict
        df 를 CSV·Parquet 로 저장하고 형식별 쓰기/읽기 평균시간·파일크기를 측정해 반환.
    print_comparison(metrics: dict, rows: int) -> None
        측정 결과를 표 형태로 출력.

변경 내역 (Changelog)
    v1.0 (2026-07-20) 최초 작성 - CSV/Parquet 저장 및 성능 비교
=============================================================================
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import pandas as pd


def _measure(fn: Callable[[], object], repeat: int) -> float:
    """fn 을 repeat 회 실행한 평균 소요 시간(초)을 반환한다.

    첫 1회는 워밍업으로 버려 지연 임포트 등 일회성 비용을 측정에서 제외한다.
    """
    fn()  # 워밍업
    start = time.perf_counter()
    for _ in range(repeat):
        fn()
    return (time.perf_counter() - start) / repeat


def _bench(writer: Callable, reader: Callable, path: Path, repeat: int) -> dict:
    """한 형식의 쓰기/읽기 평균시간(ms)과 파일 크기(KB)를 측정한다."""
    return {
        "write_ms": _measure(writer, repeat) * 1000,
        "read_ms": _measure(reader, repeat) * 1000,
        "size_kb": path.stat().st_size / 1024,
    }


def save_both(df: pd.DataFrame, csv_path: str | Path, parquet_path: str | Path) -> None:
    """df 를 CSV·Parquet 두 형식으로 저장한다 (성능 측정 없이)."""
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)


def save_and_compare(
    df: pd.DataFrame,
    csv_path: str | Path,
    parquet_path: str | Path,
    repeat: int = 100,
) -> dict:
    """df 를 CSV·Parquet 로 저장하고 형식별 쓰기/읽기 시간·크기를 측정해 반환한다."""
    csv_path, parquet_path = Path(csv_path), Path(parquet_path)
    return {
        "csv": _bench(
            lambda: df.to_csv(csv_path, index=False),
            lambda: pd.read_csv(csv_path),
            csv_path,
            repeat,
        ),
        "parquet": _bench(
            lambda: df.to_parquet(parquet_path, index=False),
            lambda: pd.read_parquet(parquet_path),
            parquet_path,
            repeat,
        ),
    }


def print_comparison(metrics: dict, rows: int) -> None:
    """저장 성능 측정 결과를 표로 출력한다."""
    print(f"\n[저장·성능 비교] {rows}행 기준 (평균)")
    print(f"  {'형식':<8}{'쓰기(ms)':>12}{'읽기(ms)':>12}{'크기(KB)':>12}")
    for fmt, m in metrics.items():
        print(
            f"  {fmt:<8}{m['write_ms']:>12.3f}{m['read_ms']:>12.3f}{m['size_kb']:>12.2f}"
        )
