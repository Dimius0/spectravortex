# rizoma_integrator.py
# Полный интегратор для всех скриптов Ризомы

import sys
import os
import importlib.util
import inspect
import time
from pathlib import Path

sys.path.append(r"C:\Program Files\SpectraVortex\Core")
from rizoma_core import init_core, get_core
from rizoma_decorators import synchronized, traced, vector_aware, in_tick

class RizomaIntegrator:
    def __init__(self, core_freq=60.0):
        self.core = init_core(core_freq)
        self.loaded_modules = {}
        self.patched_functions = {}
        
    def start(self):
        self.core.start()
        print(f"🚀 Ядро запущено ({self.core.tick.Frequency} Гц)")
        
    def stop(self):
        self.core.stop()
        print("⏹️ Ядро остановлено")
        
    def load_script(self, script_path):
        """Загружает скрипт и анализирует его структуру"""
        name = os.path.basename(script_path)
        print(f"\n📦 Загрузка: {name}")
        
        spec = importlib.util.spec_from_file_location(name.replace('.py', ''), script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        self.loaded_modules[name] = module
        return module
    
    def analyze_module(self, module):
        """Анализирует модуль и возвращает структуру"""
        structure = {
            'functions': [],
            'classes': [],
            'callable_objects': []
        }
        
        for name, obj in inspect.getmembers(module):
            if name.startswith('_'):  # Пропускаем служебные
                continue
                
            if inspect.isfunction(obj):
                structure['functions'].append(name)
                # Проверяем, можно ли вызвать без аргументов
                sig = inspect.signature(obj)
                if len(sig.parameters) == 0:
                    structure['callable_objects'].append(('function', name, obj))
                    
            elif inspect.isclass(obj):
                structure['classes'].append(name)
                # Проверяем методы класса
                if hasattr(obj, '__call__'):
                    structure['callable_objects'].append(('callable_class', name, obj))
                if hasattr(obj, 'run') and callable(getattr(obj, 'run')):
                    structure['callable_objects'].append(('class_run', name, obj))
                if hasattr(obj, 'start') and callable(getattr(obj, 'start')):
                    structure['callable_objects'].append(('class_start', name, obj))
        
        return structure
    
    def patch_functions(self, module, function_names):
        """Патчит указанные функции"""
        patched = []
        for func_name in function_names:
            if hasattr(module, func_name):
                original = getattr(module, func_name)
                if callable(original):
                    patched_func = synchronized(traced(func_name)(original))
                    setattr(module, func_name, patched_func)
                    patched.append(func_name)
        
        if patched:
            print(f"  🔧 Запатчено функций: {len(patched)}")
            if len(patched) <= 5:
                print(f"     {', '.join(patched)}")
        return patched
    
    def interactive_session(self, script_path):
        """Интерактивная сессия для работы со скриптом"""
        module = self.load_script(script_path)
        structure = self.analyze_module(module)
        
        print(f"\n📊 Анализ модуля:")
        if structure['functions']:
            print(f"  Функции: {', '.join(structure['functions'][:5])}" + 
                  (f" и ещё {len(structure['functions'])-5}" if len(structure['functions'])>5 else ""))
        
        if structure['classes']:
            print(f"  Классы: {', '.join(structure['classes'][:3])}" +
                  (f" и ещё {len(structure['classes'])-3}" if len(structure['classes'])>3 else ""))
        
        # Патчим все функции
        self.patch_functions(module, structure['functions'])
        
        if structure['callable_objects']:
            print(f"\n🎯 Доступные точки входа:")
            for i, (type_name, name, obj) in enumerate(structure['callable_objects'][:5]):
                print(f"  {i+1}. {type_name}: {name}")
            
            print("\n💡 Введите номер для запуска (или 'q' для выхода):")
            
            while True:
                choice = input(">> ").strip()
                if choice.lower() == 'q':
                    break
                
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(structure['callable_objects']):
                        type_name, name, obj = structure['callable_objects'][idx]
                        print(f"\n🚀 Запуск {name}...")
                        
                        if type_name == 'function':
                            result = obj()
                        elif type_name in ['class_run', 'class_start']:
                            instance = obj()
                            method = getattr(instance, 'run' if 'run' in type_name else 'start')
                            result = method()
                        elif type_name == 'callable_class':
                            result = obj()()
                        
                        print(f"✅ Результат: {result}")
                    else:
                        print("❌ Неверный номер")
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
        else:
            print("\n⚠️ Нет автоматических точек входа")
            print("   Модуль загружен, используй его вручную:")
            print(f"   >>> import {module.__name__}")
        
        return module

def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python rizoma_integrator.py <путь_к_скрипту>")
        print("  python rizoma_integrator.py all              # показать все доступные скрипты")
        sys.exit(1)
    
    integrator = RizomaIntegrator(60.0)
    integrator.start()
    
    try:
        if sys.argv[1] == 'all':
            # Показать все .py файлы в коммерческой папке
            commercial_path = r"C:\Users\Dim\spectravortex\commercial"
            if os.path.exists(commercial_path):
                print(f"\n📁 Доступные скрипты в {commercial_path}:")
                for file in sorted(Path(commercial_path).glob("*.py")):
                    size = file.stat().st_size
                    print(f"  {file.name} ({size} bytes)")
            else:
                print(f"❌ Папка не найдена: {commercial_path}")
        else:
            # Интерактивная сессия для конкретного скрипта
            integrator.interactive_session(sys.argv[1])
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Прервано пользователем")
    finally:
        integrator.stop()

if __name__ == "__main__":
    main()