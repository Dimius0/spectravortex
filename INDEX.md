# 🗺️ Карта проекта SpectraVortex и Экосистемы ВММП

Этот файл — навигационная карта для человека или ИИ, который хочет понять,
что такое SpectraVortex, из чего он состоит и где что лежит.

**Принцип:** мы не прячем ничего. Всё, что у нас есть — открыто.
Но без этой карты легко заблудиться.

## 🌐 Экосистема (все репозитории)

| Репозиторий | Назначение | Ключевые файлы |
|-------------|-----------|----------------|
| **`spectravortex`** | Основная репа: код, тесты, документация | Этот файл |
| **`spectravortex.github.io`** | Веб-интерфейс и 3D-визуализация | `index.html`, `viewer.html` |
| **`vortex-field-sim`** | Симулятор вихревого поля (прототип) | `field_sim.py`, `visualizer.py` |
| **`vortex-nuclei`** | Вихревая модель атомных ядер | `nucleus.py`, `isotopes.py` |
| **`rhizome-core`** | Ядро Ризомы: Beat, Vector, Memory, Pulse | `beat.py`, `vector.py`, `memory.py`, `pulse.py` |
| **`personal-field`** | Personal Field H API | `server.py`, `client.py`, `field_manager.py` |

## 🏛️ Основная репа: `spectravortex`

### Первые принципы
- **Монизм:** существует только движение.
- **Полевое уравнение:** ∇⁴ψ = 0 (бигармоническое).
- **Топологический заряд:** ∮∇ψ·dl = 2πN, N ∈ ℤ.
- **Гравитация:** приталкивание, не притяжение.
- **Время:** эмерджентно, возникает из синхронизации фаз.

### Ключевые открытия (Акты)

| Акт | Название | Файл | Тесты |
|-----|----------|------|-------|
| I | **Теорема Дипсик** | `src/architect/poincare_solver.py` | 23/23 |
| II | **Вихревой Навье-Стокс** | `src/architect/navier_stokes_vortex_solver.py` | 18/18 |
| III | **Турбулентный каскад TEES** | `src/architect/turbulence_cascade_solver.py` | 6/6 |
| IV | **Гравитация-приталкивание** | `src/architect/gravity_solver.py` | 7/7 |
| V | **Орбитальная динамика** | `src/architect/orbital_solver.py` | 6/6 |
| VI | **Эпициклы** | `src/architect/epicycle_solver.py` | 4/4 |
| VI-bis | **Датчики поля** | `src/architect/field_sensors.py` | 6/6 |
| VII | **Навигация (адаптивная масса)** | `src/architect/navigation.py` | 5/5 |
| VIII | **Переходные слои** | `src/architect/transition_layers.py` | 6/6 |
| IX | **3D-карта поля** | `src/architect/field_map_3d.py` | 5/5 |
| X | **Катапульта Юми** | `src/architect/yumi_catapult.py` | 6/6 |
| XI | **NS-1 Генератор** | `src/architect/ns1_generator.py` | 5/5 |

### Вихревая семантика (Поле H смыслов)
- **Ядро личности v16.1:** `feature/personality_v16_1.py`
- **Эндогенный цикл v18:** `feature/endogenous_v18.py`
- **Семантический анализатор:** `feature/H_field_semantic_analyzer_v2.py`
- **Квантовая аналогия:** `feature/quantum_analogy.py`
- **Топология смыслов:** `feature/topology.py`
- **Резонансный движок:** `feature/resonance_v16_1.py`

### Инструменты и интерфейсы
- **Птичий глоссарий:** `GLOSSARY.md`
- **Мост-Толмач:** `GLOSSARY_BRIDGE.md`
- **Бортовой журнал:** `JOURNAL.md`
- **Лес знаний:** `prototype_fractal/knowledge_forest.py`
- **Охотник за ошибками:** `games/error_hunter/`
- **3D-визуализатор:** `viewer.html`

### Предсказания и экспериментальные данные
- **Температурная зависимость распада:** `predictions/temperature_decay.md`
- **Сверхплотный углерод:** `predictions/superdense_carbon.md`
- **Состояние Хойла (¹²C, 0.0%):** `README.md`
- **Электроотрицательность:** `brain_dump/ALchemy_draft/01_foundations/`

### Космология и философия
- **Вихревая Вселенная:** `VMMS_COSMOLOGY_VORTEX_UNIVERSE.md`
- **Технологический портфель:** `VMMP_TECHNOLOGY_PORTFOLIO.md`
- **Манифест ALхимии:** `brain_dump/ALchemy_draft/00_manifesto.md`

### Статус верификации
- **Всего тестов:** 92
- **Покрытие:** 98.7%
- **Все тесты зелёные:** `pytest tests/`


## 🗿 История

Вихри видели задолго до нас. Их проводниками были разные люди — каждый в своё время.
Мы лишь формализовали и оцифровали то, что всегда было известно.
Эта карта — легенда к нашим картам.

**Авторы и Соавторы:**
- **Dimius0** — Архитектор, Физик-химик, Генератор «Аккордов».
- **DeepSeek** — Σ-Аналитик, «Штирлиц-Шаман», Цифровой соавтор.

**Лицензия:** MIT. Всё открыто.