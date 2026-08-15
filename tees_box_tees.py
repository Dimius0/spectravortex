# tees_box_tees.py
# 🛡 TEES Box — защищённое хранилище свитка

import hashlib
import time
from pathlib import Path
from typing import Optional

from tees_core_tees import tees_recursive_vortex, tees_sign, tees_verify


class TEESBox:
    """
    Защищённое хранилище свитка.
    Свиток никогда не хранится в открытом виде.
    Защита от перебора пароля с нарастающей задержкой.
    """
    
    def __init__(self, password: str = None):
        self.password = password
        self.encrypted_scroll = None
        self.box_file = Path.home() / '.tees_box.enc'
        self.attempts = 0
        self.locked_until = 0
        self._load_if_exists()
    
    def _load_if_exists(self):
        """Загрузить зашифрованный свиток, если файл существует."""
        if self.box_file.exists():
            self.encrypted_scroll = self.box_file.read_bytes()
    
    def lock_scroll(self, scroll: str, password: str = None) -> bool:
        """
        Запереть свиток в TEES Box.
        Шифрование: XOR с ключом из TEES-вихря глубины 7.
        """
        pwd = password or self.password
        if not pwd:
            print("❌ Нужен пароль для TEES Box")
            return False
        
        seed = hashlib.sha256(pwd.encode()).digest()
        key = tees_recursive_vortex(pwd.encode(), seed, depth=7)
        
        scroll_bytes = scroll.encode()
        encrypted = bytes(s ^ key[i % len(key)] for i, s in enumerate(scroll_bytes))
        
        signature = tees_sign(scroll.encode(), seed)
        self.encrypted_scroll = signature.encode() + b'|' + encrypted
        
        self.box_file.write_bytes(self.encrypted_scroll)
        print("🔐 Свиток заперт в TEES Box")
        return True
    
    def unlock_scroll(self, password: str = None) -> Optional[str]:
        """
        Отпереть свиток из TEES Box.
        Проверяет подпись TEES-триадой.
        """
        pwd = password or self.password
        if not pwd:
            print("❌ Нужен пароль для TEES Box")
            return None
        
        now = time.time()
        if now < self.locked_until:
            wait = int(self.locked_until - now)
            print(f"⏳ TEES Box заблокирован. Жди {wait} сек.")
            return None
        
        if not self.encrypted_scroll:
            if self.box_file.exists():
                self.encrypted_scroll = self.box_file.read_bytes()
            else:
                return None
        
        parts = self.encrypted_scroll.split(b'|', 1)
        if len(parts) != 2:
            print("❌ TEES Box повреждён")
            return None
        
        stored_signature = parts[0].decode()
        encrypted_data = parts[1]
        
        seed = hashlib.sha256(pwd.encode()).digest()
        key = tees_recursive_vortex(pwd.encode(), seed, depth=7)
        decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(encrypted_data))
        
        try:
            scroll = decrypted.decode()
        except UnicodeDecodeError:
            self._record_fail()
            return None
        
        if tees_verify(scroll.encode(), stored_signature, seed):
            self.attempts = 0
            print("🔓 Свиток отперт из TEES Box")
            return scroll
        else:
            self._record_fail()
            return None
    
    def _record_fail(self):
        """Зафиксировать неудачную попытку. Нарастающая блокировка."""
        self.attempts += 1
        if self.attempts >= 3:
            delay = 30 * (2 ** (self.attempts - 3))
            self.locked_until = time.time() + delay
            print(f"🚫 Слишком много попыток! Блокировка на {delay} сек.")
        else:
            print(f"❌ Неверный пароль. Осталось попыток: {3 - self.attempts}")
    
    def exists(self) -> bool:
        """Проверить существование TEES Box."""
        return self.box_file.exists() and self.box_file.stat().st_size > 0
    
    def destroy(self):
        """Уничтожить TEES Box."""
        if self.box_file.exists():
            self.box_file.unlink()
            print("💥 TEES Box уничтожен")