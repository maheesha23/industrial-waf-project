#!/usr/bin/env python3
"""
WAF Proof-of-Concept Test Suite
Sends benign and malicious requests against the WAF-protected endpoint
and verifies ModSecurity / OWASP CRS blocks the malicious ones while
allowing legitimate traffic through.
"""

import sys
import requests

BASE_URL = "http://localhost"
TIMEOUT = 10

# Each test case: (name, method, path, kwargs for requests, expected_status)
TEST_CASES = [
    (
        "Benign Request (Homepage)",
        "GET",
        "/",
        {},
        200,
    ),
    (
        "SQL Injection (Login Bypass)",
        "POST",
        "/rest/user/login",
        {
            "json": {"email": "admin@juice-sh.op' OR 1=1--", "password": "x"},
            "headers": {"Content-Type": "application/json"},
        },
        403,
    ),
    (
        "SQL Injection (UNION-based)",
        "GET",
        "/rest/products/search",
        {"params": {"q": "' UNION SELECT * FROM Users--"}},
        403,
    ),
    (
        "Cross-Site Scripting (XSS)",
        "GET",
        "/rest/products/search",
        {"params": {"q": "<img src=x onerror=alert(1)>"}},
        403,
    ),
    (
        "Path Traversal",
        "GET",
        "/rest/products/search",
        {"params": {"q": ";cat /etc/passwd"}},
        403,
    ),
    (
        "Command Injection",
        "GET",
        "/rest/products/search",
        {"params": {"q": "`id`"}},
        403,
    ),
]


def run_tests():
    results = []
    print(f"\n{'='*60}")
    print(f"  WAF Proof-of-Concept Test Suite")
    print(f"  Target: {BASE_URL}")
    print(f"{'='*60}\n")

    for name, method, path, kwargs, expected in TEST_CASES:
        url = f"{BASE_URL}{path}"
        try:
            response = requests.request(
                method, url, timeout=TIMEOUT, **kwargs
            )
            actual = response.status_code
            passed = actual == expected
            results.append(passed)

            status_icon = "✅" if passed else "❌"
            print(f"{status_icon} {name}")
            print(f"   Expected: HTTP {expected} | Got: HTTP {actual}")
            if not passed:
                print(f"   ⚠️  Unexpected result — check WAF configuration")
            print()

        except requests.exceptions.RequestException as e:
            results.append(False)
            print(f"❌ {name}")
            print(f"   Request failed: {e}\n")

    print(f"{'='*60}")
    passed_count = sum(results)
    total_count = len(results)
    print(f"  Results: {passed_count}/{total_count} tests passed")
    print(f"{'='*60}\n")

    return passed_count == total_count


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)