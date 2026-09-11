# diag_jpl_limit.py
import requests

BASE_URL = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"

# Тестируем разные лимиты
limits_to_test = [10, 50, 100, 500, 1000, 2000, 5000]

for limit in limits_to_test:
    params = {
        "fields": "full_name,a,e,i",
        "sb-group": "neo",
        "limit": limit,
    }
    
    try:
        r = requests.get(BASE_URL, params=params, timeout=60)
        if r.status_code == 200:
            data = r.json()
            count = len(data.get('data', []))
            print(f"✅ limit={limit}: OK (объектов: {count})")
        else:
            print(f"❌ limit={limit}: {r.status_code} — {r.text[:100]}")
    except Exception as e:
        print(f"❌ limit={limit}: {e}")

# Проверяем total count
print(f"\n📊 Всего NEO:")
params = {"fields": "pdes", "sb-group": "neo"}
try:
    r = requests.get(BASE_URL, params=params, timeout=60)
    if r.status_code == 200:
        data = r.json()
        print(f"   Всего: {len(data.get('data', []))}")
except Exception as e:
    print(f"   ❌ {e}")