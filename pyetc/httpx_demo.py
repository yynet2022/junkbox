import logging
import httpx

logging.basicConfig(level=logging.DEBUG)

mounts = {
    "all://": httpx.HTTPTransport(proxy="http://localhost:8080", verify=False),
    "all://localhost": None,
    "all://127.0.0.1": None,
    "all://*example.com": None,
}

client = httpx.Client(mounts=mounts, verify=False)

try:
    r = client.get("http://www.google.com")
    print(r)
    print(r.text[:100])
except Exception as e:
    print(f"{e.__class__.__name__}: {e}")
print("-------")

try:
    r = client.get("http://localhost:8000/")
    print(r)
    print(r.text[:100])
except Exception as e:
    print(f"{e.__class__.__name__}: {e}")
print("-------")

try:
    r = client.get("http://127.0.0.1:9999/")
    print(r)
    print(r.text[:100])
except Exception as e:
    print(f"{e.__class__.__name__}: {e}")
print("-------")
