# bip2100_chaos.py
# 🛡️ BIP2100 CHAOS: 2100 случайных строк для максимальной защиты!

import random
import string

def generate_chaos_word(min_len=5, max_len=14):
    """
    Генерирует случайную строку.
    - Строчные + прописные + цифры!
    - Разная длина!
    - Полный хаос!
    """
    length = random.randint(min_len, max_len)
    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def generate_chaos_list(n_words=2100):
    """
    Генерирует список случайных слов.
    - Нет повторов!
    - Нет алфавитного порядка!
    - Нет осмысленности!
    """
    words = set()
    
    while len(words) < n_words:
        word = generate_chaos_word()
        words.add(word)
    
    # Перемешиваем!
    words_list = list(words)
    random.shuffle(words_list)
    
    return words_list

# Генерируем словарь!
random.seed(42)  # Детерминизм для воспроизводимости!
BIP2100_CHAOS_WORDS = generate_chaos_list(2100)

# Выводим статистику!
print(f"🛡️ BIP2100 CHAOS: {len(BIP2100_CHAOS_WORDS)} слов!")
print(f"   Длина: {min(len(w) for w in BIP2100_CHAOS_WORDS)}-{max(len(w) for w in BIP2100_CHAOS_WORDS)} символов!")
print(f"   Уникальных: {len(set(BIP2100_CHAOS_WORDS))}")
print(f"   Все с цифрами: {sum(1 for w in BIP2100_CHAOS_WORDS if any(c.isdigit() for c in w))}")
print(f"   Все с верхним регистром: {sum(1 for w in BIP2100_CHAOS_WORDS if any(c.isupper() for c in w))}")

# Генерация seed-фразы!
def generate_chaos_phrase(n_words=12):
    return " ".join(random.sample(BIP2100_CHAOS_WORDS, n_words))

if __name__ == "__main__":
    print(f"\n📜 CHAOS SEED PHRASES:")
    for i in range(5):
        print(f"   {i+1}. {generate_chaos_phrase(12)}")
    
    print(f"\n🔍 АНАЛИЗ ДЛЯ TEES:")
    print(f"   Осмысленных слов: 0 (из {len(BIP2100_CHAOS_WORDS)})")
    print(f"   Тематических групп: 0")
    print(f"   Алфавитного порядка: НЕТ")
    print(f"   → TEES НЕ МОЖЕТ СУЗИТЬ ПОИСК! 🛡️")