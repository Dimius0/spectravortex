# diag_jpl_endpoints.py
import requests

endpoints = [
    "https://ssd-api.jpl.nasa.gov/sbdb_query.api",
    "https://ssd.jpl.nasa.gov/api/sbdb_query.api",
    "https://ssd.jpl.nasa.gov/sbdb_query.api",
]

params = {
    "fields": "full_name,a,e,i",
    "sb-group": "neo",
    "limit": 10,
}

for url in endpoints:
    print(f"\n🔍 Проверка: {url}")
    try:
        r = requests.get(url, params=params, timeout=30)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            print(f"   ✅ Работает!")
            data = r.json()
            print(f"   Объектов: {len(data.get('data', []))}")
        else:
            print(f"   ❌ {r.text[:200]}")
    except requests.exceptions.ReadTimeout:
        print(f"   ⏱️ Timeout")
    except Exception as e:
        print(f"   ❌ {e}")