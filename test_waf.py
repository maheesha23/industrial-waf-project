#!/usr/bin/env python3
"""
WAF Proof-of-Concept Test Suite
Sends benign and malicious requests against the WAF-protected endpoint
and verifies ModSecurity / OWASP CRS blocks the malicious ones while
allowing legitimate traffic through. Also verifies Nginx rate limiting
correctly throttles a burst of rapid requests (DoS mitigation).
"""

import sys
import time
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

# Rate limit test config - must exceed general_limit's burst allowance
# (burst=20 in nginx-templates/default.conf.template) to trigger a 429
RATE_LIMIT_REQUEST_COUNT = 40
RATE_LIMIT_TARGET_PATH = "/"


def run_standard_tests():
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

    return results


def run_rate_limit_test():
    """
    Sends a rapid burst of requests to trigger Nginx's limit_req rate
    limiter. Passes if at least one 429 Too Many Requests response is
    observed before the burst allowance is exhausted.
    """
    print(f"{'='*60}")
    print(f"  Rate Limit / DoS Mitigation Test")
    print(f"  Sending {RATE_LIMIT_REQUEST_COUNT} rapid requests to {RATE_LIMIT_TARGET_PATH}")
    print(f"{'='*60}\n")

    url = f"{BASE_URL}{RATE_LIMIT_TARGET_PATH}"
    status_counts = {}
    got_429 = False

    for i in range(1, RATE_LIMIT_REQUEST_COUNT + 1):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            code = response.status_code
            status_counts[code] = status_counts.get(code, 0) + 1
            if code == 429:
                got_429 = True
        except requests.exceptions.RequestException as e:
            print(f"   Request {i} failed: {e}")

    print("   Response breakdown:")
    for code, count in sorted(status_counts.items()):
        print(f"     HTTP {code}: {count}")
    print()

    if got_429:
        print("✅ Rate Limit Exceeded (DoS)")
        print("   Expected: at least one HTTP 429 | Got: HTTP 429 present\n")
    else:
        print("❌ Rate Limit Exceeded (DoS)")
        print("   Expected: at least one HTTP 429 | Got: none — rate limiting may not be active\n")

    # Brief pause to let the rate limit bucket drain before any further tests
    time.sleep(2)

    return got_429


def run_tests():
    standard_results = run_standard_tests()
    rate_limit_result = run_rate_limit_test()

    all_results = standard_results + [rate_limit_result]

    print(f"{'='*60}")
    passed_count = sum(all_results)
    total_count = len(all_results)
    print(f"  Results: {passed_count}/{total_count} tests passed")
    print(f"{'='*60}\n")

    return passed_count == total_count


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)