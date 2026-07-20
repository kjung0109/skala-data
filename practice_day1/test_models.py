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
=============================================================================
"""

import pytest
from pydantic import ValidationError

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
