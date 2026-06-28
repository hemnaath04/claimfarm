"""Pytest-wide test configuration.

R-2: the app binds the IP rate limit at import time from
`RATE_LIMIT_PER_MINUTE`. The full suite issues many requests from the same
TestClient host; on a fast run that could trip a 429 and make unrelated
tests flaky (and, now that CI fails on test errors, break the build). Pin a
very high limit for the test session so rate-limiting never interferes with
functional assertions. Dedicated rate-limit behavior is covered by its own
focused checks that set the limit explicitly.

This runs before any test module imports `app.main`, so the value is in
effect when the middleware is constructed.
"""

import os

os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "100000")
# Tests must never depend on the production-insecure dev-link echo unless a
# test opts in explicitly (see tests/test_sec007_dev_links.py).
os.environ.setdefault("AUTH_DEV_LINKS", "false")
