# diag_jpl_fields2.py
import requests

BASE_URL = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"

# Список полей для проверки
fields_to_test = [
    "full_name",
    "a,e,i",
    "a,e,i,om,w,ma",
    "a,e,i,om,w,ma,moid",
    "a,e,i,om,w,ma,moid,H",
    "a,e,i,om,w,ma,t_jup",
    "a,e,i,om,w,ma,moid,H,t_jup",
    "pdes",
    "full_name,a,e,i,om,w,ma,t_jup,moid,H",
]

for fields in fields_to_test:
    print(f"\n🔍 Тест: fields={fields}")
    
    params = {
        "fields": fields,
        "sb-group": "neo",
        "limit": 5,
    }
    
    try:
        r = requests.get(BASE_URL, params=params, timeout=30)
        print(f"   Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            count = len(data.get('data', []))
            print(f"   ✅ Работает! Объектов: {count}")
            if count > 0:
                print(f"   Пример: {data['data'][0][:3]}...")
        else:
            print(f"   ❌ {r.text[:150]}")
    except Exception as e:
        print(f"   ❌ {e}")

# Тест с t_jup отдельно
print("\n" + "="*60)
print("🔍 ТЕСТ: только t_jup")
print("="*60)
params = {
    "fields": "full_name,t_jup",
    "sb-group": "neo",
    "limit": 5,
}
try:
    r = requests.get(BASE_URL, params=params, timeout=30)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Работает!")
        print(f"   Fields: {data.get('fields')}")
        print(f"   Пример: {data['data'][0] if data.get('data') else 'нет'}")
    else:
        print(f"   ❌ {r.text[:200]}")
except Exception as e:
    print(f"   ❌ {e}")