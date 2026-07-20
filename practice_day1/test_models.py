# -*- coding: utf-8 -*-
"""
=============================================================================
[Day1 종합] test_models — Pydantic 스키마 검증 테스트 (pytest)
=============================================================================
프로그램 설명
    models.py 의 각 스키마에 대해 정상 파싱과 타입·범위 위반 시 예외 발생을 검증한다.
    네트워크 없이 실제 응답 구조를 축약한 샘플로 테스트한다.

함수 구성 (파라미터 · 기능)
    sample_weather() / sample_country() / sample_ip() : 응답 구조 축약 픽스처.
    test_* : 정상 파싱 및 검증 실패(ValidationError/ValueError) 케이스.

변경 내역 (Changelog)
    v1.0 (2026-07-20) 최초 작성 - 3개 모델 정상/오류 검증 테스트
    v1.1 (2026-07-20) validate_all 파이프라인 레벨 예외 처리 테스트 추가
    v1.2 (2026-07-20) fetch_json 재시도(백오프) 테스트 추가
=============================================================================
"""

import asyncio

import httpx
import pytest
from pydantic import ValidationError

from collect import fetch_json
from main import validate_all
from models import CountryInfo, IpInfo, WeatherForecast, WeatherHour


@pytest.fixture
def sample_weather() -> dict:
    """Open-Meteo 응답 구조 축약 (시간 2건)."""
    return {
        "latitude": 37.55,
        "longitude": 127.0,
        "timezone": "Asia/Seoul",
        "hourly": {
            "time": ["2026-07-20T00:00", "2026-07-20T01:00"],
            "temperature_2m": [26.3, 25.9],
            "precipitation_probability": [10, 0],
        },
    }


@pytest.fixture
def sample_country() -> dict:
    """Countries.dev 응답 구조 축약."""
    return {
        "name": "Korea (Republic of)",
        "capital": "Seoul",
        "region": "Asia",
        "subregion": "Eastern Asia",
        "population": 51780579,
        "area": 100210,
        "alpha3Code": "KOR",
    }


@pytest.fixture
def sample_ip() -> dict:
    """ip-api 응답 구조 축약."""
    return {
        "status": "success",
        "query": "8.8.8.8",
        "country": "United States",
        "countryCode": "US",
        "city": "Ashburn",
        "regionName": "Virginia",
        "lat": 39.03,
        "lon": -77.5,
        "isp": "Google LLC",
        "timezone": "America/New_York",
    }


# --- 정상 파싱 ---------------------------------------------------------------
def test_weather_from_api_ok(sample_weather):
    forecast = WeatherForecast.from_api(sample_weather)
    assert len(forecast.hours) == 2
    assert forecast.timezone == "Asia/Seoul"


def test_country_from_api_ok(sample_country):
    country = CountryInfo.from_api(sample_country)
    assert country.alpha3_code == "KOR"
    assert country.population > 0


def test_ip_from_api_ok(sample_ip):
    ip = IpInfo.from_api(sample_ip)
    assert ip.query == "8.8.8.8"
    assert ip.country_code == "US"


# --- 타입·범위 검증 실패 -----------------------------------------------------
def test_precipitation_out_of_range():
    with pytest.raises(ValidationError):
        WeatherHour(time="t", temperature_2m=20.0, precipitation_probability=150)


def test_country_population_must_be_positive(sample_country):
    bad = {**sample_country, "population": 0}
    with pytest.raises(ValidationError):
        CountryInfo.from_api(bad)


def test_ip_status_failure_raises():
    with pytest.raises(ValueError):
        IpInfo.from_api({"status": "fail", "message": "reserved range"})


# --- 파이프라인 레벨 예외 처리 ------------------------------------------------
def test_validate_all_handles_bad_record(sample_weather, sample_country, sample_ip):
    """한 API가 불량이어도 나머지는 통과하고 파이프라인이 죽지 않는다."""
    bad_country = {**sample_country, "population": -5}  # 인구 음수 → 검증 실패
    raw = {"weather": sample_weather, "country": bad_country, "ip": sample_ip}

    forecast, country, ip = validate_all(raw)

    assert forecast is not None and ip is not None  # 정상 데이터는 통과
    assert country is None  # 불량 데이터만 걸러짐 (예외 처리로 None)


# --- 수집 재시도(백오프) -----------------------------------------------------
def test_fetch_json_retries_transient_error():
    """일시적 5xx 오류는 재시도 후 성공한다 (네트워크 없이 MockTransport)."""
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 2:
            return httpx.Response(503)  # 첫 시도: 일시적 오류
        return httpx.Response(200, json={"ok": True})

    async def run() -> tuple[str, dict | None]:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            return await fetch_json(client, "test", "http://x", retries=2, backoff=0)

    name, data = asyncio.run(run())
    assert data == {"ok": True}
    assert calls["n"] == 2  # 1회 실패 + 1회 성공(재시도 동작 확인)
