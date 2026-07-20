# -*- coding: utf-8 -*-
"""
=============================================================================
[Day1 종합] collect — httpx + asyncio 비동기 수집
=============================================================================
프로그램 설명
    3개 공개 API를 asyncio.gather() 로 동시에 호출해 JSON 응답을 모은다.
    개별 요청 실패는 건너뛰고(부분 실패 허용), 성공분만 dict 로 반환한다.

함수 구성 (파라미터 · 기능)
    fetch_json(client: httpx.AsyncClient, name: str, url: str) -> tuple[str, dict | None]
        단일 API 호출. 성공 시 (name, JSON), 실패 시 (name, None) 반환·경고 출력.
    collect_all(endpoints: dict[str, str] = API_ENDPOINTS) -> dict[str, dict]
        endpoints 를 gather(return_exceptions=True)로 동시 수집해 성공분만 반환.
    collect() -> dict[str, dict]
        collect_all() 을 asyncio.run 으로 실행하는 동기 진입점.

변경 내역 (Changelog)
    v1.0 (2026-07-20) 최초 작성 - 3개 API 비동기 동시 수집
=============================================================================
"""

from __future__ import annotations

import asyncio

import httpx

HTTP_TIMEOUT = 10  # 초

# 수집 대상 API (name → URL)
API_ENDPOINTS: dict[str, str] = {
    "weather": (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=37.5665&longitude=126.9780"
        "&hourly=temperature_2m,precipitation_probability"
        "&forecast_days=3&timezone=Asia/Seoul"
    ),
    "country": "https://countries.dev/alpha/KOR",
    "ip": "http://ip-api.com/json/8.8.8.8",
}


async def fetch_json(
    client: httpx.AsyncClient, name: str, url: str
) -> tuple[str, dict | None]:
    """단일 API를 호출해 (name, JSON) 을 반환한다 (실패 시 (name, None)+경고)."""
    try:
        r = await client.get(url)
        r.raise_for_status()
        return name, r.json()
    except (httpx.HTTPError, ValueError) as e:
        print(f"[WARN] {name} 수집 실패: {e}")
        return name, None


async def collect_all(endpoints: dict[str, str] = API_ENDPOINTS) -> dict[str, dict]:
    """endpoints 를 asyncio.gather 로 동시 수집해 성공한 응답만 dict 로 반환한다."""
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        tasks = [fetch_json(client, name, url) for name, url in endpoints.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    collected: dict[str, dict] = {}
    for res in results:
        if isinstance(res, Exception):  # gather 안전망: 예기치 못한 예외
            print(f"[WARN] 예기치 못한 수집 오류: {res}")
            continue
        name, data = res
        if data is not None:
            collected[name] = data
    return collected


def collect() -> dict[str, dict]:
    """비동기 수집을 동기적으로 실행하는 진입점 (asyncio.run)."""
    return asyncio.run(collect_all())
