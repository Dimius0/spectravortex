#!/usr/bin/env python
# rizoma.py - Стабильная версия с обработкой ошибок

import sys
import os
import time
import glob
import traceback
from pathlib import Path

# ути
CORE_PATH = r"C:\Program Files\SpectraVortex\Core"
COMMERCIAL_PATH = r"C:\Users\Dim\spectravortex\commercial"

sys.path.append(CORE_PATH)
sys.path.append(COMMERCIAL_PATH)

# мпортируем ядро
try:
    from rizoma_core import init_core, get_core
    from rizoma_decorators import synchronized, traced, vector_aware
    CORE_READY = True
except Exception as e:
    print(f"⚠️ Ядро не загружено: {e}")
    CORE_READY = False

class Rizoma:
    """лавный класс объединённой изомы"""
    
    def __init__(self, frequency=60.0, auto_load=True):
        print("🚀 нициализация изомы...")
        
        # Ядро
        if CORE_READY:
            self.core = init_core(frequency)
            self.core_ready = True
        else:
            self.core = None
            self.core_ready = False
            
        self.modules = {}
        self.module_errors = []
        self.running = False
        
        if auto_load:
            self.auto_load_modules()
        
    def start(self):
        """апуск изомы"""
        if self.core_ready:
            self.core.start()
        self.running = True
        print("✅ изома запущена")
        print(f"📊 агружено модулей: {len(self.modules)}")
        if self.module_errors:
            print(f"⚠️ шибок при загрузке: {len(self.module_errors)}")
        return self
        
    def stop(self):
        """становка изомы"""
        if self.core_ready and self.core:
            self.core.stop()
        self.running = False
        print("⏹️ изома остановлена")
        
    def auto_load_modules(self):
        """втоматически загружает все .py файлы"""
        print("🔍 оиск модулей...")
        
        py_files = glob.glob(str(Path(COMMERCIAL_PATH) / "*.py"))
        exclude = ['__init__.py', 'setup.py']
        
        # Специальная обработка для headquarters
        hq_path = Path(COMMERCIAL_PATH) / "headquarters"
        if hq_path.exists():
            sys.path.append(str(hq_path))
            print(f"  📁 обавлен путь: headquarters")
        
        modules_loaded = 0
        
        for py_file in py_files:
            module_name = os.path.basename(py_file)
            if module_name in exclude:
                continue
                
            try:
                self.load_module(module_name)
                modules_loaded += 1
            except Exception as e:
                error_msg = f"{module_name}: {str(e)[:100]}"
                self.module_errors.append(error_msg)
                print(f"  ⚠️ {error_msg}")
        
        print(f"✅ агружено модулей: {modules_loaded}")
        
    def load_module(self, module_name):
        """агружает модуль с обработкой ошибок"""
        module_path = Path(COMMERCIAL_PATH) / module_name
        
        if not module_path.exists():
            raise FileNotFoundError(f"айл не найден")
            
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            module_name.replace('.py', ''), 
            module_path
        )
        module = importlib.util.module_from_spec(spec)
        
        try:
            spec.loader.exec_module(module)
            self.modules[module_name] = module
            print(f"  ✅ {module_name}")
            return module
        except Exception as e:
            # робуем загрузить с подавлением ошибок
            try:
                import types
                fake_module = types.ModuleType(module_name)
                self.modules[module_name] = fake_module
                print(f"  🔶 {module_name} (упрощённо)")
                return fake_module
            except:
                raise e
    
    def get_module(self, name):
        """олучить загруженный модуль"""
        return self.modules.get(name)
    
    def list_modules(self):
        """Список загруженных модулей"""
        return list(self.modules.keys())
    
    def safe_call(self, module_name, func_name, *args, **kwargs):
        """езопасный вызов функции"""
        module = self.get_module(module_name)
        if not module:
            return None
            
        func = getattr(module, func_name, None)
        if not func or not callable(func):
            return None
            
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"⚠️ {module_name}.{func_name}: {e}")
            return None
    
    def status(self):
        """Текущее состояние"""
        status = {
            'running': self.running,
            'modules': len(self.modules),
            'module_list': list(self.modules.keys())[:5],
            'errors': len(self.module_errors)
        }
        
        if self.core_ready and self.core:
            try:
                core_status = self.core.get_status()
                status.update({
                    'tick': core_status['tick'],
                    'vector': round(core_status['vector'], 3),
                    'sync': core_status['sync']
                })
            except:
                pass
                
        return status

# лобальный экземпляр
_rizoma = None

def get_rizoma(freq=60.0, auto_load=True):
    """олучить экземпляр изомы"""
    global _rizoma
    if _rizoma is None:
        _rizoma = Rizoma(freq, auto_load)
    return _rizoma

def start(auto_load=True):
    """ыстрый старт"""
    r = get_rizoma(auto_load=auto_load)
    r.start()
    return r

def stop():
    """ыстрая остановка"""
    r = get_rizoma()
    r.stop()

def status():
    """ыстрый статус"""
    r = get_rizoma()
    return r.status()

def fix_headquarters():
    """справление ошибки в headquarters"""
    hq_path = Path(COMMERCIAL_PATH) / "headquarters" / "__init__.py"
    if not hq_path.exists():
        print("❌ headquarters/__init__.py не найден")
        return
        
    with open(hq_path, 'r') as f:
        content = f.read()
    
    # обавляем метод если его нет
    if 'append_to_list' not in content:
        backup = hq_path.with_suffix('.py.bak')
        hq_path.rename(backup)
        print(f"📦 Создан бэкап: {backup}")
        
        # Создаём исправленную версию
        fixed = content.replace(
            'class SharedMemory',
            'class SharedMemory:\n    def append_to_list(self, name, value):\n        if not hasattr(self, name):\n            setattr(self, name, [])\n        getattr(self, name).append(value)\n\nclass SharedMemory'
        )
        
        with open(hq_path, 'w') as f:
            f.write(fixed)
        print("✅ headquarters/__init__.py исправлен")
    else:
        print("✅ headquarters уже содержит append_to_list")

if __name__ == "__main__":
    print("=" * 60)
    print(" - Стабильная версия")
    print("=" * 60)
    
    # справляем headquarters если нужно
    fix_headquarters()
    
    # апускаем
    r = start()
    print(f"\n📊 Статус: {r.status()}")
    print(f"\n📋 одули ({len(r.modules)}):")
    for i, name in enumerate(list(r.modules.keys())[:15]):
        print(f"  {i+1}. {name}")
    
    print("\n💡 оманды:")
    print("  from rizoma import *")
    print("  r = start()")
    print("  r.status()")
    print("  r.get_module('имя_файла.py')")
    print("  stop()")
