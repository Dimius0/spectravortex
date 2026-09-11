#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛰️ fetch_real_nea.py v6
Скачивание NEO через разбиение по большой полуоси (a).
"""

import requests
import json
import time
import numpy as np

BASE_URL = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"

def fetch_by_a_range(a_min, a_max, chunk_size=500):
    """Скачивает NEO в диапазоне a."""
    print(f"\n📦 Диапазон a: {a_min} - {a_max} AU")
    
    params = {
        "fields": "full_name,a,e,i,om,w,ma,t_jup,moid,H",
        "sb-group": "neo",
        "sb-cdata": json.dumps({"AND": [f"a|GE|{a_min}", f"a|LT|{a_max}"]}),
        "limit": chunk_size,
    }
    
    try:
        r = requests.get(BASE_URL, params=params, timeout=300)
        r.raise_for_status()
        data = r.json()
        
        if "data" not in data:
            return []
        
        fields = data["fields"]
        rows = data["data"]
        
        print(f"   ✅ Получено: {len(rows)}")
        
        return [dict(zip(fields, row)) for row in rows]
    except Exception as e:
        print(f"   ❌ {e}")
        return []


def fetch_all_neo():
    """Скачивает все NEO через разбиение по a."""
    print("🚀 Загрузка NEO через разбиение по a")
    
    all_objects = []
    
    # Диапазоны a (0.5 - 7 AU, покрывает все NEO)
    a_ranges = [
        (0.5, 1.0),
        (1.0, 1.2),
        (1.2, 1.4),
        (1.4, 1.6),
        (1.6, 1.8),
        (1.8, 2.0),
        (2.0, 2.5),
        (2.5, 3.0),
        (3.0, 4.0),
        (4.0, 5.0),
        (5.0, 7.0),
    ]
    
    for a_min, a_max in a_ranges:
        batch = fetch_by_a_range(a_min, a_max, chunk_size=500)
        all_objects.extend(batch)
        time.sleep(1)
    
    # Сохраняем
    if all_objects:
        output_file = "nea_real_data.json"
        with open(output_file, "w") as f:
            json.dump(all_objects, f, indent=2)
        print(f"\n💾 Сохранено: {output_file} ({len(all_objects):,} объектов)")
    
    return all_objects


if __name__ == "__main__":
    start = time.time()
    nea_data = fetch_all_neo()
    elapsed = time.time() - start
    
    if nea_data:
        print(f"\n⏱️ Время: {elapsed:.1f} сек")
        print(f"📊 Всего: {len(nea_data):,}")
        
        # Статистика
        t_j_values = []
        moid_values = []
        
        for nea in nea_data:
            try:
                t_j = float(nea.get('t_jup', 0))
                if t_j != 0:
                    t_j_values.append(t_j)
            except:
                pass
            try:
                moid = float(nea.get('moid', 0))
                if moid != 0:
                    moid_values.append(moid)
            except:
                pass
        
        if t_j_values:
            t_j = np.array(t_j_values)
            print(f"\n📊 T_J:")
            print(f"   Объектов: {len(t_j):,}")
            print(f"   Мин: {t_j.min():.3f}, Макс: {t_j.max():.3f}")
            print(f"   Среднее: {t_j.mean():.3f}")
        
        if moid_values:
            moid = np.array(moid_values)
            print(f"\n📊 MOID:")
            print(f"   Опасных (MOID<0.05): {np.sum(moid < 0.05):,}")
    else:
        print("❌ Нет данных")