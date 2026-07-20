# -*- coding: utf-8 -*-
"""
=============================================================================
[Day1 종합] models — 수집 데이터 Pydantic v2 스키마 (타입·범위 검증)
=============================================================================
프로그램 설명
    3개 공개 API 응답에서 필요한 필드를 추출해 타입·범위를 검증하는 스키마.
    각 모델은 원시 JSON(dict)을 받아 검증 객체로 변환하는 from_api() 를 제공한다.

구성 (모델 · 검증 규칙)
    WeatherHour(BaseModel)
        Open-Meteo 시간대별 1건. time(비어있지 않음),
        temperature_2m(-90~60°C), precipitation_probability(0~100%, None 허용).
    WeatherForecast(BaseModel)
        서울 예보. latitude(-90~90), longitude(-180~180), timezone, hours: list[WeatherHour].
        from_api(data: dict) -> WeatherForecast : hourly 병렬 배열을 시간별 레코드로 변환.
    CountryInfo(BaseModel)
        한국 국가 정보. name·capital 필수, population>0, area>0, alpha3_code(3자).
        from_api(data: dict) -> CountryInfo : 응답에서 필요한 필드만 추출.
    IpInfo(BaseModel)
        IP 지역 정보. query(IP)·country_code(2자)·lat(-90~90)·lon(-180~180) 등.
        from_api(data: dict) -> IpInfo : status!='success' 이면 ValueError.

변경 내역 (Changelog)
    v1.0 (2026-07-20) 최초 작성 - 3개 API 추출 필드 스키마 및 from_api 정의
=============================================================================
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Open-Meteo : 날씨 예보
# ---------------------------------------------------------------------------
class WeatherHour(BaseModel):
    """시간대별 예보 1건 (기온·강수확률)."""

    time: str = Field(min_length=1)                                  # ISO8601 시각
    temperature_2m: float = Field(ge=-90, le=60)                     # 기온(°C) 물리 범위
    precipitation_probability: int | None = Field(default=None, ge=0, le=100)  # 강수확률(%)


class WeatherForecast(BaseModel):
    """Open-Meteo 응답에서 추출한 서울 예보."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: str = Field(min_length=1)
    hours: list[WeatherHour]

    @classmethod
    def from_api(cls, data: dict) -> WeatherForecast:
        """응답의 hourly 병렬 배열(time/temp/precip)을 시간별 레코드로 변환한다."""
        h = data["hourly"]
        hours = [
            WeatherHour(time=t, temperature_2m=temp, precipitation_probability=prob)
            for t, temp, prob in zip(
                h["time"], h["temperature_2m"], h["precipitation_probability"]
            )
        ]
        return cls(
            latitude=data["latitude"],
            longitude=data["longitude"],
            timezone=data["timezone"],
            hours=hours,
        )


# ---------------------------------------------------------------------------
# Countries.dev : 국가 정보
# ---------------------------------------------------------------------------
class CountryInfo(BaseModel):
    """한국 국가 정보 (필요 필드만 추출)."""

    name: str = Field(min_length=1)
    capital: str = Field(min_length=1)
    region: str = Field(min_length=1)
    subregion: str | None = None
    population: int = Field(gt=0)
    area: float = Field(gt=0)
    alpha3_code: str = Field(min_length=3, max_length=3)

    @classmethod
    def from_api(cls, data: dict) -> CountryInfo:
        """Countries.dev 응답에서 필요한 필드만 추출해 검증한다."""
        return cls(
            name=data["name"],
            capital=data["capital"],
            region=data["region"],
            subregion=data.get("subregion"),
            population=data["population"],
            area=data["area"],
            alpha3_code=data["alpha3Code"],
        )


# ---------------------------------------------------------------------------
# ip-api : IP 기반 지역 정보
# ---------------------------------------------------------------------------
class IpInfo(BaseModel):
    """IP 기반 지역 정보 (필요 필드만 추출)."""

    query: str = Field(min_length=1)                        # 조회한 IP
    country: str = Field(min_length=1)
    country_code: str = Field(min_length=2, max_length=2)
    city: str = Field(min_length=1)
    region_name: str = Field(min_length=1)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    isp: str = Field(min_length=1)
    timezone: str = Field(min_length=1)

    @classmethod
    def from_api(cls, data: dict) -> IpInfo:
        """ip-api 응답에서 필요한 필드만 추출한다 (status!='success' 시 ValueError)."""
        if data.get("status") != "success":
            raise ValueError(f"ip-api 조회 실패: {data.get('message', 'unknown')}")
        return cls(
            query=data["query"],
            country=data["country"],
            country_code=data["countryCode"],
            city=data["city"],
            region_name=data["regionName"],
            lat=data["lat"],
            lon=data["lon"],
            isp=data["isp"],
            timezone=data["timezone"],
        )
