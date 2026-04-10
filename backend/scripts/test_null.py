"""Test null byte via HTTP to running server."""
import httpx

c = httpx.Client(base_url="http://127.0.0.1:8000", timeout=10, trust_env=False)
# First: normal request to confirm the server works
r = c.post("/api/v1/auth/register", json={"username": "normal_testxxx", "password": "Test1234!"})
print(f"Normal: {r.status_code}")

# New client for null byte test
c2 = httpx.Client(base_url="http://127.0.0.1:8000", timeout=10, trust_env=False)
r2 = c2.post("/api/v1/auth/register", json={"username": "null\x00test", "password": "Test1234!"})
print(f"NullByte: {r2.status_code} {r2.text[:300]}")
c2.close()

# Test connection still works after
c3 = httpx.Client(base_url="http://127.0.0.1:8000", timeout=10, trust_env=False)
r3 = c3.post("/api/v1/auth/register", json={"username": "after_null_test", "password": "Test1234!"})
print(f"After: {r3.status_code}")
c3.close()
