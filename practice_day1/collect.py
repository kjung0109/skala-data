# -*- coding: utf-8 -*-
"""
=============================================================================
[Day1 종합] collect — httpx + asyncio 비동기 수집
=============================================================================
프로그램 설명
    3개 공개 API를 asyncio.gather() 로 동시에 호출해 JSON 응답을 모은다.
    개별 요청 실패는 건너뛰고(부분 실패 허용), 성공분만 dict 로 반환한다.

함수 구성 (파라미터 · 기능)
    fetch_json(client, name, url, retries=MAX_RETRIES, backoff=BACKOFF_BASE)
              -> tuple[str, dict | None]
        단일 API 호출. 일시적 HTTP 오류는 백오프 재시도, 실패 시 (name, None).
    collect_all(endpoints: dict[str, str] = API_ENDPOINTS) -> dict[str, dict]
        endpoints 를 gather(return_exceptions=True)로 동시 수집해 성공분만 반환.
    collect() -> dict[str, dict]
        collect_all() 을 asyncio.run 으로 실행하는 동기 진입점.

변경 내역 (Changelog)
    v1.0 (2026-07-20) 최초 작성 - 3개 API 비동기 동시 수집
    v1.1 (2026-07-20) 일시적 HTTP 오류 백오프 재시도 추가
=============================================================================
"""

from __future__ import annotations

import asyncio

import httpx

HTTP_TIMEOUT = 10   # 요청 타임아웃(초)
MAX_RETRIES = 2     # 일시적 오류 시 최대 재시도 횟수
BACKOFF_BASE = 0.5  # 재시도 대기(초) = BACKOFF_BASE * 시도횟수

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
    client: httpx.AsyncClient,
    name: str,
    url: str,
    retries: int = MAX_RETRIES,
    backoff: float = BACKOFF_BASE,
) -> tuple[str, dict | None]:
    """단일 API를 호출해 (name, JSON) 을 반환한다.

    일시적 HTTP 오류(5xx·타임아웃 등)는 선형 백오프로 재시도하고,
    JSON 파싱 실패는 재시도 없이 즉시 실패 처리한다. 최종 실패 시 (name, None).
    """
    for attempt in range(retries + 1):
        try:
            r = await client.get(url)
            r.raise_for_status()
            return name, r.json()
        except httpx.HTTPError as e:  # 네트워크·타임아웃·5xx 등 (재시도 가치 있음)
            if attempt < retries:
                wait = backoff * (attempt + 1)
                print(
                    f"[WARN] {name} 요청 실패 → {wait:.1f}s 후 재시도"
                    f"({attempt + 1}/{retries}): {e}"
                )
                await asyncio.sleep(wait)
                continue
            print(f"[ERROR] {name} 수집 실패 (재시도 {retries}회 초과): {e}")
            return name, None
        except ValueError as e:  # JSON 파싱 실패 → 재시도 무의미
            print(f"[ERROR] {name} 응답 파싱 실패: {e}")
            return name, None
    return name, None  # 도달하지 않음 (안전용)


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
