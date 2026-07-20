# -*- coding: utf-8 -*-
"""
=============================================================================
[Day1 종합] main — 데이터 수집 미니 파이프라인 오케스트레이션
=============================================================================
프로그램 설명
    수집(collect) → 검증(models) → 저장·성능비교(storage) 를 순서대로 실행한다.
      1) asyncio 로 3개 API 동시 수집
      2) Pydantic 모델로 타입·범위 검증 (실패 시 예외 처리)
      3) 날씨 시간대별 데이터를 CSV·Parquet 로 저장하고 읽기/쓰기 성능 비교
      4) 국가·IP 정보는 metadata.json 으로 저장

함수 구성 (파라미터 · 기능)
    build_weather_df(forecast: WeatherForecast) -> pd.DataFrame
        검증된 예보의 시간별 레코드를 DataFrame 으로 변환.
    validate_all(raw: dict) -> tuple[WeatherForecast|None, CountryInfo|None, IpInfo|None]
        수집 raw 를 각 모델로 검증 (개별 try/except, 실패 시 None).
    save_metadata(country, ip, path: Path) -> None
        국가·IP 검증 결과를 JSON 으로 저장 (ensure_ascii=False).
    run_pipeline(raw: dict) -> None
        수집 이후 단계(검증→저장→비교)를 수행 (오프라인 테스트 가능).
    main() -> None
        비동기 수집 후 run_pipeline 실행하는 진입점.

변경 내역 (Changelog)
    v1.0 (2026-07-20) 최초 작성 - 수집·검증·저장·비교 파이프라인 연결
=============================================================================
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from collect import collect_all
from models import CountryInfo, IpInfo, WeatherForecast
from storage import print_comparison, save_and_compare

BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "output"


def build_weather_df(forecast: WeatherForecast) -> pd.DataFrame:
    """검증된 예보의 시간별 레코드를 DataFrame 으로 변환한다."""
    return pd.DataFrame(h.model_dump() for h in forecast.hours)


def _safe(label: str, fn) -> object | None:
    """검증 함수 fn 을 실행하고, 실패 시 오류를 출력한 뒤 None 을 반환한다."""
    try:
        obj = fn()
    except (ValidationError, ValueError, KeyError) as e:
        print(f"  [ERROR] {label} 검증 실패: {e}")
        return None
    print(f"  [OK] {label} 검증 통과")
    return obj


def validate_all(raw: dict) -> tuple:
    """수집 raw 를 각 Pydantic 모델로 검증한다 (개별 예외 처리, 실패 시 None)."""
    forecast = _safe("weather", lambda: WeatherForecast.from_api(raw["weather"]))
    country = _safe("country", lambda: CountryInfo.from_api(raw["country"]))
    ip = _safe("ip", lambda: IpInfo.from_api(raw["ip"]))
    return forecast, country, ip


def save_metadata(country: CountryInfo | None, ip: IpInfo | None, path: Path) -> None:
    """국가·IP 검증 결과를 JSON 으로 저장한다 (한글 보존)."""
    meta = {
        "country": country.model_dump() if country else None,
        "ip": ip.model_dump() if ip else None,
    }
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def run_pipeline(raw: dict) -> None:
    """수집 이후 단계(검증 → 저장 → 성능 비교)를 수행한다."""
    OUTPUT.mkdir(exist_ok=True)

    print("\n[2] 스키마 검증")
    forecast, country, ip = validate_all(raw)

    if forecast is not None:
        df = build_weather_df(forecast)
        metrics = save_and_compare(df, OUTPUT / "weather.csv", OUTPUT / "weather.parquet")
        print_comparison(metrics, len(df))
    else:
        print("\n[WARN] 날씨 데이터 없음 → 저장·비교 생략")

    save_metadata(country, ip, OUTPUT / "metadata.json")
    print(f"\n[OK] 파이프라인 완료 → 결과: {OUTPUT}")


def main() -> None:
    """비동기 수집 후 파이프라인을 실행하는 진입점."""
    print("[1] 비동기 수집 시작 (3개 API 동시 호출)")
    raw = asyncio.run(collect_all())
    print(f"  수집 성공: {list(raw)}")
    run_pipeline(raw)


if __name__ == "__main__":
    main()
