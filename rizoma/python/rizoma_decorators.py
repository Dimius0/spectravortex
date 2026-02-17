# rizoma_decorators.py
# Декораторы для интеграции старых скриптов с новым ядром

import functools
from rizoma_core import get_core

def synchronized(func):
    """
    Декоратор: функция выполняется синхронно с тактом.
    Если ядро не запущено — просто выполняет функцию.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        core = get_core()
        if core and core.running:
            tick_before = core.get_tick()
            result = func(*args, **kwargs)
            tick_after = core.get_tick()
            core.trace.Push(func.__name__, "sync_exec", tick_after - tick_before, tick_after)
            return result
        else:
            return func(*args, **kwargs)
    return wrapper

def traced(trace_type="info"):
    """
    Декоратор: записывает факт выполнения функции в TraceBuffer.
    Использование: @traced("scan") или @traced()
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            core = get_core()
            if core and core.running:
                tick = core.get_tick()
                result = func(*args, **kwargs)
                core.trace.Push(func.__name__, trace_type, 1.0, tick)
                return result
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator

def vector_aware(func):
    """
    Декоратор: передаёт текущий вектор в функцию.
    Функция должна принимать параметр current_vector.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        core = get_core()
        if core and core.running:
            kwargs['current_vector'] = core.conductor.CurrentVector
        return func(*args, **kwargs)
    return wrapper

def in_tick(func):
    """
    Декоратор: функция выполняется только один раз за такт.
    Повторные вызовы в том же такте игнорируются.
    """
    last_tick = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        core = get_core()
        if not core or not core.running:
            return func(*args, **kwargs)
            
        current_tick = core.get_tick()
        func_id = id(func)
        
        if func_id not in last_tick or last_tick[func_id] != current_tick:
            last_tick[func_id] = current_tick
            result = func(*args, **kwargs)
            core.trace.Push(func.__name__, "in_tick", 1.0, current_tick)
            return result
        else:
            # Уже выполняли в этом такте
            return None
    return wrapper

def crisis_boundary(enter_reason=None):
    """
    Декоратор: отмечает вход и выход из кризисной фазы.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            core = get_core()
            if not core or not core.running:
                return func(*args, **kwargs)
                
            tick_before = core.get_tick()
            vector_before = core.conductor.CurrentVector
            
            if enter_reason:
                core.historian.EnterCrisis(enter_reason, vector_before, tick_before)
            
            result = func(*args, **kwargs)
            
            tick_after = core.get_tick()
            vector_after = core.conductor.CurrentVector
            
            core.historian.ExitCrisis(vector_after, tick_after)
            
            return result
        return wrapper
    return decorator

# Тестовый пример использования
if __name__ == "__main__":
    from rizoma_core import init_core
    import time
    
    core = init_core(10.0)
    core.start()
    
    @synchronized
    @traced("test")
    def test_function(x):
        return x * 2
    
    @vector_aware
    def vector_function(x, current_vector=None):
        print(f"Вектор: {current_vector}, аргумент: {x}")
        return x * (current_vector or 1)
    
    print("Тест декораторов:")
    for i in range(3):
        print(f"  test_function(5) = {test_function(5)}")
        vector_function(3)
        time.sleep(0.3)
    
    core.stop()
    print("✅ Тест завершён")