#!/usr/bin/env python3

"""Basic WAF validation checks for benign, SQLi, and XSS traffic."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Dict, List

import requests


BASE_URL = os.environ.get("BASE_URL", "http://localhost")
TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class TestCase:
    name: str
    params: Dict[str, str]
    expected_status: int


def run_request(session: requests.Session, test_case: TestCase) -> int:
    response = session.get(BASE_URL, params=test_case.params, timeout=TIMEOUT_SECONDS)
    return response.status_code


def main() -> int:
    test_cases: List[TestCase] = [
        TestCase(name="benign", params={"q": "hello-world"}, expected_status=200),
        TestCase(name="sqli", params={"q": "' OR 1=1--"}, expected_status=403),
        TestCase(name="xss", params={"q": "<script>alert(1)</script>"}, expected_status=403),
    ]

    failures: List[str] = []

    with requests.Session() as session:
        for test_case in test_cases:
            try:
                status_code = run_request(session, test_case)
            except requests.RequestException as exc:
                failures.append(f"{test_case.name}: request failed ({exc})")
                continue

            verdict = "PASS" if status_code == test_case.expected_status else "FAIL"
            print(f"{verdict} {test_case.name}: expected {test_case.expected_status}, got {status_code}")

            if status_code != test_case.expected_status:
                failures.append(
                    f"{test_case.name}: expected {test_case.expected_status}, got {status_code}"
                )

    if failures:
        print("\nWAF validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nWAF validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())