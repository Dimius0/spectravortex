# merge_logs.py (v2.2 — честный парсер под формат лога)
# Склеивает два лога (Чистый и Скорпион) в одну сводную таблицу с дельтами.
import sys

def parse_line(line):
    # Формат строки: "   101 | d=5.140 | E=11389425365.5 | Активны: ... | 7.6s"
    parts = line.strip().split('|')
    if len(parts) < 4:
        return None
    try:
        step = int(parts[0].strip())
        d = float(parts[1].strip().split('=')[1])
        e = float(parts[2].strip().split('=')[1])
        groups = parts[3].strip()
        return step, d, e, groups
    except:
        return None

def load_log(filename):
    data = {}
    encodings = ['utf-16', 'utf-8']
    for enc in encodings:
        try:
            with open(filename, 'r', encoding=enc) as f:
                for line in f:
                    parsed = parse_line(line)
                    if parsed:
                        step, d, e, groups = parsed
                        data[step] = (d, e, groups)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    return data

if len(sys.argv) >= 3:
    file_clean = sys.argv[1]
    file_scorp = sys.argv[2]
else:
    file_clean = 'log_clean_500k.txt'
    file_scorp = 'log_scorpion_500k.txt'

print(f"Чистый: {file_clean}")
print(f"Скорпион: {file_scorp}")

clean = load_log(file_clean)
scorp = load_log(file_scorp)

print(f"Загружено точек: Чистый={len(clean)}, Скорпион={len(scorp)}")

all_steps = sorted(set(clean.keys()) | set(scorp.keys()))

with open('comparison_table.txt', 'w', encoding='utf-8') as out:
    header = (f"{'Step':>6} | {'d_clean':>8} | {'E_clean':>14} | {'d_scorp':>8} | {'E_scorp':>14} | "
              f"{'dd':>8} | {'dE':>14}")
    out.write(header + "\n")
    out.write("-" * len(header) + "\n")
    
    prev_e_clean = None
    prev_e_scorp = None
    
    for step in all_steps:
        d_c, e_c, g_c = clean.get(step, (float('nan'), float('nan'), ''))
        d_s, e_s, g_s = scorp.get(step, (float('nan'), float('nan'), ''))
        
        delta_d = d_s - d_c if not (d_s != d_s or d_c != d_c) else float('nan')
        delta_e = e_s - e_c if not (e_s != e_s or e_c != e_c) else float('nan')
        
        out.write(f"{step:6} | {d_c:8.3f} | {e_c:14.1f} | {d_s:8.3f} | {e_s:14.1f} | "
                  f"{delta_d:+8.3f} | {delta_e:+14.1f}\n")

print("Готово! Сводная таблица сохранена в comparison_table.txt")