import json

input_file = 'data/initial_frame_474201.json'
output_file = 'data/checkpoint_474201.json'

print(f"Читаем {input_file}...")
with open(input_file, 'r') as f:
    frame = json.load(f)

# Создаём структуру чекпоинта
checkpoint = {
    "metadata": {
        "completed_steps": frame['step'],
        "d_min": frame['d_min'],
        "source": "extracted from log_trajectories_3d.json"
    },
    "frames": [frame]  # массив с одним кадром
}

print(f"Конвертируем в чекпоинт...")
with open(output_file, 'w') as f:
    json.dump(checkpoint, f, indent=2)

print(f"Готово! Чекпоинт сохранён в '{output_file}'")