import os
import re
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.adzuna.com"

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "").strip()
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "").strip()


COUNTRY_MAP = {
    "united kingdom": "gb",
    "uk": "gb",
    "great britain": "gb",
    "england": "gb",
    "germany": "de",
    "deutschland": "de",
    "united states": "us",
    "usa": "us",
    "poland": "pl",
    "lithuania": "lt",
    "latvia": "lv",
    "estonia": "ee",
    "netherlands": "nl",
    "spain": "es",
    "france": "fr",
    "italy": "it",
}


def _normalize_country(country: Optional[str]) -> str:
    if not country:
        return "gb"

    value = country.strip().lower()

    if len(value) == 2 and re.fullmatch(r"[a-z]{2}", value):
        return value

    return COUNTRY_MAP.get(value, "gb")


def _ensure_credentials() -> None:
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        raise RuntimeError(
            "Adzuna credentials are missing. Add ADZUNA_APP_ID and ADZUNA_APP_KEY to backend/.env"
        )


def _map_job(item: Dict[str, Any]) -> Dict[str, Any]:
    company = (item.get("company") or {}).get("display_name") or "Unknown company"
    location = (item.get("location") or {}).get("display_name") or "Unknown location"
    category = (item.get("category") or {}).get("label") or "Other"

    salary_min = item.get("salary_min")
    salary_max = item.get("salary_max")

    salary = None
    if salary_min or salary_max:
        salary = {
            "min": salary_min,
            "max": salary_max,
            "currency": item.get("salary_currency") or None,
        }

    description = item.get("description") or ""

    work_mode = ""
    lowered = description.lower()

    if "remote" in lowered:
        work_mode = "remote"
    elif "hybrid" in lowered:
        work_mode = "hybrid"
    elif "onsite" in lowered or "on-site" in lowered or "office" in lowered:
        work_mode = "onsite"

    contract_time = item.get("contract_time") or ""

    return {
        "job_id": str(item.get("id") or ""),
        "title": item.get("title") or "Untitled",
        "company_name": company,
        "location_text": location,
        "country": "",
        "category": category,
        "description": description,
        "created": item.get("created") or "",
        "contract_time": contract_time,
        "contract_type": item.get("contract_type") or "",
        "work_mode": work_mode,
        "salary": salary,
        "source_url": item.get("redirect_url") or "",
    }


def search_adzuna(
    query: str = "",
    country: str = "gb",
    page: int = 1,
    results_per_page: int = 20,
    sort_by: str = "date",
) -> Dict[str, Any]:
    _ensure_credentials()

    country_code = _normalize_country(country)
    page = max(1, int(page))
    results_per_page = max(1, min(int(results_per_page), 50))

    url = f"{BASE_URL}/v1/api/jobs/{country_code}/search/{page}"

    params: Dict[str, Any] = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": (query or "software developer").strip(),
        "results_per_page": results_per_page,
        "content-type": "application/json",
    }

    if sort_by == "date":
        params["sort_by"] = "date"
    else:
        params["sort_by"] = "relevance"

    response = requests.get(url, params=params, timeout=20)

    if not response.ok:
        raise RuntimeError(
            f"Adzuna request failed: {response.status_code} {response.text[:300]}"
        )

    data = response.json()
    raw_results = data.get("results") or []

    jobs = [_map_job(item) for item in raw_results]

    return {
        "count": int(data.get("count") or 0),
        "jobs": jobs,
    }


def fetch_jobs(
    query: str,
    country: str = "gb",
    page: int = 1,
    results_per_page: int = 20,
) -> List[Dict[str, Any]]:
    return search_adzuna(
        query=query,
        country=country,
        page=page,
        results_per_page=results_per_page,
    ).get("jobs", [])