import json

# Имя исходного JSON-файла с траекториями
input_file = 'data/log_trajectories_3d.json'
# Номер шага, который мы хотим извлечь (глубокий аттрактор)
target_step = 474201
# Имя выходного файла с одним кадром
output_file = f'data/initial_frame_{target_step}.json'

print(f"Читаем {input_file}...")
with open(input_file, 'r') as f:
    data = json.load(f)

print(f"Всего кадров в файле: {len(data)}")

# Ищем кадр с нужным шагом
frame = None
for frm in data:
    if frm.get('step') == target_step:
        frame = frm
        break

if frame is None:
    print(f"ОШИБКА: Кадр с шагом {target_step} не найден.")
    print(f"Первый шаг: {data[0].get('step')}, последний: {data[-1].get('step')}")
else:
    print(f"Кадр найден! d_min = {frame.get('d_min', 'N/A')}")
    
    # Сохраняем этот кадр как начальное условие
    with open(output_file, 'w') as f:
        json.dump(frame, f, indent=2)
    
    print(f"Готово! Файл '{output_file}' сохранён.")