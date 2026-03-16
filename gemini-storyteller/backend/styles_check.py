import httpx
try:
    r = httpx.get('http://localhost:8000/styles')
    print(r.json())
except Exception as e:
    print(f"Error: {e}")
