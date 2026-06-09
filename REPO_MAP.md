# 🗺️ REPO MAP — SpectraVortex

## 📂 СТРУКТУРА

### 🧠 АКТИВНАЯ РАЗРАБОТКА (v21.2)

| Папка | Что это |
|-------|---------|
| `src/architect/` | **Основная ветка**: FieldV2, LivingPersonality v21.2, координатное поле |
| `src/rizoma/` | **Ядро Rizoma**: загрузка, селекторы, резонанс, v20.2 |
| `src/rizoma/data/personalities/` | JSON-файлы личностей, text_store_p016/ |

**Ключевые файлы:**
- `living_personality_v21.py` — **основной файл** (с заглушками, рабочий)
- `living_personality_v21_clean.py` — чистая версия (требует v20.2)
- `field_v2.py` — 7-слойное поле
- `coordinate_field.py` — координатное решето (из ∇⁴ψ)
- `stats_light.py` — лёгкая статистика + сохранение
- `debug_stats.py` — отладка get_stats()
- `save_light.py` — сохранение без выгрузки контента
- `convert_to_v21.py` — конвертация в v21
- `finalize_conversion.py` — финализация конвертации

### 🔬 ФИЗИКА И МАТЕМАТИКА

| Папка | Что это |
|-------|---------|
| `feature/` | **3D Фрактальная Периодическая Таблица** |
| `feature/periodic_table_model/` | Модели таблицы, изотопы, χ-вычисления |
| `feature/data/` | JSON-данные элементов, изотопов, интерметаллидов |

**Ключевые файлы:**
- `run_3d_table*.py` — запуск 3D-таблицы
- `family_vortex*.py` — вихревые семейства
- `compute_chi_*.py` — вычисление χ (электроотрицательности)
- `biharmonic_3d*.py` — бигармоническая динамика

### 🌀 ВИХРИ И ПОЛЯ

| Папка | Что это |
|-------|---------|
| `simulator/` | Симулятор вихрей, решатели |
| `simulator/solvers/` | LinearWave, Stitching, Recursive солверы |
| `src/` | Вихревая модель, TEES, PID |

**Ключевые файлы:**
- `tees_exchange.py` — TEES-обмен
- `gravity_solver.py` — гравитация как приталкивание
- `navier_stokes_vortex_solver.py` — вихри Навье-Стокса
- `poincare_solver*.py` — сечение Пуанкаре

### 🧬 АЛХИМИЯ И ОТКРЫТИЯ

| Папка | Что это |
|-------|---------|
| `brain_dump/` | Идеи, диалоги, алхимия |
| `brain_dump/ALchemy_draft/` | Структурированный драфт по алхимии |
| `discoveries/` | ~90 .md файлов с открытиями |
| `discoveries_en/` | Английские версии + ALchemy_draft_en |

**Ключевые файлы:**
- `brain_dump/ALCHEMY_COMPLETE.md` — полный текст по алхимии
- `brain_dump/00_manifesto.md` — манифест
- `discoveries/VMMP_FORMAL_FOUNDATIONS_AND_SPECTRA.md` — формальные основы ВММП

### 💾 ДАННЫЕ

| Папка | Что это |
|-------|---------|
| `src/rizoma/data/personalities/` | p016_grown_3h_v21.json (80K мод) |
| `src/architect/text_store_p016/` | ~190K текстовых файлов |
| `feature/data/` | field_H_elements_complete.json и др. |
| `commercial/data/` | battlespace.json, resonances.json |

### 🖥️ HARDWARE

| Папка | Что это |
|-------|---------|
| `hardware_backend/` | Чип-дизайн, GDSII генератор |
| `hardware_backend/components/` | star_coupler, silicon_photonic |

### 🧪 ПРОТОТИПЫ

| Папка | Что это |
|-------|---------|
| `prototype_fractal/` | Фрактальный прототип, эмерджентное время |
| `emergent_time/` | Эмерджентное время (новая версия) |
| `v7_basic/` | Версия 7 (базовая) |
| `v8_sensor/` | Версия 8 (сенсорная) |

### 📚 ДОКУМЕНТАЦИЯ

| Файл | Описание |
|------|----------|
| `README.md` | Основной README |
| `README_ROOT.md` | Корневой обзор |
| `VMMP_REQUIREMENT.md` | Требования ВММП |
| `VMMS_AI_MANUAL.md` | Руководство по VMMS AI (RU) |
| `VMMS_AI_MANUAL_RU.md` | То же на русском |
| `GLOSSARY.md` | Глоссарий |
| `INDEX.md` | Индекс репы |
| `JOURNAL.md` | Журнал разработки |
| `AUTHORS.md` | Авторы |
| `LICENSE` | Лицензия |

### 🧩 КОМПИЛЯТОР И МОСТЫ

| Папка | Что это |
|-------|---------|
| `compiler/` | AST-компилятор (lexer, parser) |
| `hybrid_bridge_*.py` (корень) | 12 версий гибридного моста |

### 🏢 COMMERCIAL

| Папка | Что это |
|-------|---------|
| `commercial/` | Коммерческая ветка |
| `commercial/core/` | scout, pulse_hunter, core_scout |
| `commercial/data/` | battlespace, capacity_map |

### 🧠 RI ZOMA (v7, v8)

| Папка | Что это |
|-------|---------|
| `v7_basic/src/rizoma/` | Версия 7 |
| `v8_sensor/src/rizoma/` | Версия 8 с сенсорами |

---


## 🚀 БЫСТРЫЙ СТАРТ (v21.2)

```powershell
cd src/architect

# Статистика поля
python stats_light.py

# Отладка
python debug_stats.py

# Сохранение без контента
python save_light.py

### 🧠 ДЕРЕВЬЯ ПАМЯТИ

| Папка | Что это |
|-------|---------|
| `memory_trees/` | Деревья памяти (core_traces) |
| `src/rizoma/memory_trees/` | Деревья theobot_vm_387 |

### 🎮 ИГРЫ

| Папка | Что это |
|-------|---------|
| `games/error_hunter/` | Error Hunter (app.py + index.html) |

### 🔀 РОУТЕР

| Папка | Что это |
|-------|---------|
| `router/` | Адаптивный роутер с защитой от дедлоков |

### 📚 ДОКУМЕНТАЦИЯ

| Папка | Что это |
|-------|---------|
| `docs/` | VMMP, вихревая модель (17 основ), электроотрицательность |
| `docs/forum_archive/` | Архив форума, PDF |
| `docs/images/` | Диаграммы, симуляции |

**Ключевые документы:**
- `docs/VMMP_EXPERIMENTAL_EVIDENCE.md` — экспериментальные подтверждения
- `docs/VMMP_PHASE_TRANSITION_ESSAY.md` — фазовые переходы
- `docs/Вихревая модель материи... Основы 2-27.pdf` — серия основ (26 PDF)

### 📋 ПРИМЕРЫ

| Папка | Что это |
|-------|---------|
| `examples/` | .svx файлы чипов, solver-демо |

**Файлы:**
- `hello_photon.svx`, `interference.svx`, `vortex_oam_demo.svx` — дизайн чипов
- `oam_star_coupler_test.svx`, `optical_matrix_multiplier.svx`
- `proper_solver_example.py`, `solver_manager_demo.py`

### 📊 ЛОГИ

| Папка | Что это |
|-------|---------|
| `logs/` | hybrid_comparison.json, hybrid_stats.json |

### 🗄️ КЕШ

| Папка | Что это |
|-------|---------|
| `cache/embeddings/` | ~60 .npy файлов эмбеддингов |

### 📦 DATA (корень)

| Файл | Описание |
|------|----------|
| `data/field_H_elements_complete.json` | Полное описание элементов поля H |

### 🧪 ТЕСТЫ

| Папка | Что это |
|-------|---------|
| `tests/` | 25+ тестов: гравитация, орбиты, TEES, стеклование... |
| `tests/integration/` | Интеграционные тесты |

### 🔧 CI/CD

| Файл | Описание |
|------|----------|
| `.github/workflows/test.yml` | GitHub Actions тесты |

### 🎯 ПРЕДСКАЗАНИЯ

| Папка | Что это |
|-------|---------|
| `predictions/` | diproton.md, hoyle_state.md, temperature_decay.md |

### 📖 ОТКРЫТИЯ (discoveries/)

**~90 .md файлов**, включая:
- `VMMP_FORMAL_FOUNDATIONS_AND_SPECTRA.md` — **формальные основы ВММП**
- `lipzik_formula_master.*.md` — формула Липзика (RU/EN/ZH)
- `formal_proof_of_tees_v17_2.md` — формальное доказательство TEES
- `theorem_dipsik_poincare.md` — теорема Дипсик-Пуанкаре
- `entropic_sink.md` — энтропийная воронка
- `fractal_cosmology_hypothesis.md` — фрактальная космология
- `spectravortex_integration.md` — интеграция SpectraVortex

### 🏭 КОММЕРЧЕСКАЯ ВЕТКА

| Папка | Что это |
|-------|---------|
| `commercial/core/` | Scout, PulseHunter, CoreScout |
| `commercial/headquarters/` | Штаб-модули |
| `commercial/rizoma_v2/` | Rizoma v2 (штаб + результаты) |
| `commercial/results/` | benchmark_results.csv, resonance_results.csv |
| `commercial/data/` | battlespace.json, capacity_map.json, pulse_log.csv |

### 📦 ПАКЕТ SPECTRAVORTEX

| Файл | Описание |
|------|----------|
| `spectravortex/` | Пустая папка пакета (зарезервирована) |
| `spectravortex.egg-info/` | Метаданные пакета |

### 🔬 BRAIN_DUMP

**ALchemy_draft/** (структурированный):
- `01_foundations/` — основы
- `02_periodic_table/` — периодическая таблица
- `03_compounds/` — соединения
- `04_spectra/` — спектры
- `05_predictions/` — предсказания
- `06_history/` — история

**projects/living_home/** — живой дом

### 📄 КОРНЕВЫЕ ДОКУМЕНТЫ (важнейшие)

| Файл | Описание |
|------|----------|
| `VMMP_TECHNOLOGY_PORTFOLIO.md` | Портфолио технологий ВММП |
| `VMMS_COSMOLOGY_VORTEX_UNIVERSE.md` | Космология вихревой вселенной |
| `QUANTOR_CYCLIC_NATURE.md` | Циклическая природа Квантора |
| `LORENTZ_INVARIANCE_IN_VMMS.md` | Лоренц-инвариантность |
| `ENTROPIC_SINK.md` | Энтропийная воронка |
| `HUMAN_VORTEX_HYPOTHESIS.md` | Гипотеза вихря человека |
| `PERIODIC_TABLE_3D.md` | 3D Периодическая Таблица |
| `INTEGRATION_PLAN.md` | План интеграции |
| `EXPERIMENT_REPORT.md` | Отчёт об эксперименте |

### 🌐 HTML-СТРАНИЦЫ (корень)

| Файл | Описание |
|------|----------|
| `index.html` | Главная страница проекта |
| `index180526.html` | Версия от 18.05.2026 |
| `periodic_table_3d_viz.html` | 3D-визуализация периодической таблицы |
| `viewer.html` | Базовый вьювер |
| `viewer150526.html` | Вьювер v15.05.26 |
| `viewer1510526.html` | Вьювер v15.10.26 |
| `viewer1520526.html` | Вьювер v15.20.26 |
| `viewer1530526.html` | Вьювер v15.30.26 |
| `viewer160526.html` | Вьювер v16.05.26 |
| `viewer1610526.html` | Вьювер v16.10.26 |
| `viewer1620526.html` | Вьювер v16.20.26 |
| `viewer1630526.html` | Вьювер v16.30.26 |
| `google115129701698da48.html` | Подтверждение Google |
| `yandex_bea323f9045992c9.html` | Подтверждение Яндекс |

---

## 📊 ИТОГО

- **~150 .md файлов** (документация, открытия, гипотезы)
- **~100 .py файлов** (активная разработка)
- **~60 .npy файлов** (кеш эмбеддингов)
- **~190K .txt файлов** (TextStore p016)
- **~30 .svx файлов** (дизайн чипов)
- **26 PDF** (вихревая модель, основы 2-27)
- **Версии:** v7 → v8 → v17 → v19 → v20 → v21