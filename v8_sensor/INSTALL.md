# Установка и запуск SpectraVortex Sensor

---

## 🇷🇺 Русская версия

### Системные требования

| Компонент | Минимально | Рекомендуемо |
|-----------|------------|--------------|
| Python | 3.8+ | 3.10+ |
| RAM | 512 МБ | 1 ГБ |
| Диск | 500 МБ | 1 ГБ |
| ОС | Windows/Linux/macOS | Windows/Linux/macOS |

### Установка

#### 1. Клонирование репозитория

```bash
git clone https://github.com/Dimius0/spectravortex.git
cd spectravortex/v8_sensor
2. Создание виртуального окружения (рекомендуется)
bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
3. Установка зависимостей
bash
pip install -r requirements_sensor.txt
4. Дополнительные зависимости
Для голосового ввода (микрофон):

bash
# Windows
pip install pyaudio

# Linux
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio

# macOS
brew install portaudio
pip install pyaudio
Запуск
Базовый тест (текстовая адаптация)
bash
python src/examples/sensor_demo.py
Голосовая адаптация (требуется микрофон)
bash
python src/examples/voice_demo.py
Mesh-сеть (децентрализованная синхронизация)
bash
python src/examples/mesh_demo.py
Проверка установки
bash
python -c "import whisper; print('Whisper OK')"
python -c "import sentence_transformers; print('Sentence Transformers OK')"
python -c "import pyaudio; print('PyAudio OK')"
🇬🇧 English Version
System Requirements
Component	Minimum	Recommended
Python	3.8+	3.10+
RAM	512 MB	1 GB
Disk	500 MB	1 GB
OS	Windows/Linux/macOS	Windows/Linux/macOS
Installation
1. Clone Repository
bash
git clone https://github.com/Dimius0/spectravortex.git
cd spectravortex/v8_sensor
2. Create Virtual Environment (recommended)
bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
3. Install Dependencies
bash
pip install -r requirements_sensor.txt
4. Additional Dependencies
For voice input (microphone):

bash
# Windows
pip install pyaudio

# Linux
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio

# macOS
brew install portaudio
pip install pyaudio
Running
Basic Test (text adaptation)
bash
python src/examples/sensor_demo.py
Voice Adaptation (requires microphone)
bash
python src/examples/voice_demo.py
Mesh Network (decentralized sync)
bash
python src/examples/mesh_demo.py
Verify Installation
bash
python -c "import whisper; print('Whisper OK')"
python -c "import sentence_transformers; print('Sentence Transformers OK')"
python -c "import pyaudio; print('PyAudio OK')"
🛠️ Устранение проблем / Troubleshooting
Проблема: ModuleNotFoundError: No module named 'whisper'
Решение: Установите openai-whisper

bash
pip install openai-whisper
Проблема: [WinError 10038] при остановке сети
Решение: Нормальное поведение, игнорируйте. Сеть корректно останавливается.

Проблема: Микрофон не работает
Решение: Проверьте, что микрофон подключен и не используется другим приложением.

Проблема: Медленная загрузка моделей
Решение: Первый запуск загружает модели (80 МБ для sentence-transformers, 74 МБ для whisper). Последующие запуски быстрее.

📊 Размер моделей / Model Sizes
Модель	Размер	Назначение
sentence-transformers (all-MiniLM-L6-v2)	80 МБ	Семантический анализ
whisper (base)	74 МБ	Распознавание речи
whisper (tiny)	39 МБ	Лёгкая версия
whisper (small)	244 МБ	Точная версия
🚀 Быстрый старт за 5 минут / Quick Start in 5 Minutes
bash
# 1. Установка
pip install numpy openai-whisper sentence-transformers

# 2. Запуск
cd src/examples
python sensor_demo.py
🦌 Лицензия / License
MIT

📖 Подробнее / More Info
README.md — общее описание

../README_ROOT.md — корневой README

v7_basic/ — базовая версия без сенсоров