# TEES — Emergent Physical Fingerprint

**Вихревой отпечаток на основе турбулентности Навье-Стокса**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> ⚠️ Это не хеш-функция. Это физический отпечаток. Не для production.

## Что это

TEES превращает входную строку в уникальный вихревой отпечаток:
вход → поле → вихрь → параметры вихря → fingerprint

Необратимость обеспечивается физикой (уравнение Навье-Стокса), а не математикой (XOR, сдвиги).

## Результаты на 1034 Bitcoin-адресах

- Естественная стабильность (VSM > 0.7): **30%**
- После оптимизации: **26%**
- Всего стабильных: **56%**
- Необратимость (≥3/4 proofs): **100%**

## Быстрый старт

```bash
git clone https://github.com/Dimius0/spectravortex
cd tees-fingerprint
pip install -r requirements.txt
python3 tees_biharmonic_v19.py
Зависимости
Python 3.8+

numpy, scipy, scikit-learn

Как работает
Из входных данных генерируется турбулентное поле

Поле эволюционирует согласно вихрю Ламба-Озеена

RANSAC оценивает циркуляцию (Gamma) и стабильность (VSM)

Если VSM > 0.7 — вихрь стабилен, отпечаток надёжен

Если VSM < 0.7 — включается адаптивная оптимизация

Ключевые метрики
VSM (Vortex Stability Metric):

> 0.7 — стабильный вихрь

0.3–0.7 — переходная зона

< 0.3 — шум

Необратимость (4 критерия):

correlation_loss, entropy_gain, hash_mismatch, ill_posed

Ограничения
❌ Не хеш-функция (нет collision resistance)

❌ Медленно (~56 сек/адрес на CPU)

✅ Proof-of-concept физического примитива

✅ Потенциал для аппаратной реализации (микрофлюидика)

Лицензия
MIT — делай что хочешь.

Цитирование
bibtex
@software{tees2026,
  title = {TEES: Emergent Physical Fingerprint},
  year = {2026},
  url = https://github.com/Dimius0/spectravortex
}