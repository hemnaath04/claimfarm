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

# Signals app.config NOT to read the developer's `.env` (which may hold a real
# RESEND_API_KEY). Must be set before app.config is imported anywhere.
os.environ["CLAIMFARM_TEST"] = "1"

os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "100000")
# Tests must never depend on the production-insecure dev-link echo unless a
# test opts in explicitly (see tests/test_sec007_dev_links.py).
os.environ.setdefault("AUTH_DEV_LINKS", "false")

# Settings load from `.env` (env_file=".env"), which on a developer machine may
# hold a real RESEND_API_KEY. Force email/SMS transports OFF for the whole test
# session so sign-up / reset / magic-link tests never fire real outbound email
# (which would spam inboxes and burn the provider quota). Force-set (not
# setdefault) so they win over any value in `.env`; env vars outrank the file.
os.environ["RESEND_API_KEY"] = ""
os.environ["SENDGRID_API_KEY"] = ""
