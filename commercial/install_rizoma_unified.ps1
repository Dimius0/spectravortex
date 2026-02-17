# install_rizoma_unified.ps1
# Единая установка Ризомы: скелет + глаза + уши
# Версия: 2.0.0
# Принцип: не чиним 96%, достраиваем

Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║  🚀 РИЗОМА: ЕДИНАЯ СБОРКА                                    ║" -ForegroundColor Magenta
Write-Host "║  Принцип: не чиним 96% - достраиваем скелет, глаза, уши     ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta

# 1. Проверка прав
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ Запустите PowerShell от имени администратора" -ForegroundColor Red
    exit 1
}

# 2. Директории
$basePath = "C:\Program Files\SpectraVortex"
$modulesPath = "$basePath\Modules"
$binPath = "$basePath\Bin"
$configPath = "C:\ProgramData\SpectraVortex\Config"
$logPath = "C:\ProgramData\SpectraVortex\Logs"
$corePath = "$basePath\Core"

$folders = @($basePath, $modulesPath, $binPath, $configPath, $logPath, $corePath,
    "$modulesPath\TickGenerator", "$modulesPath\TraceBuffer", "$modulesPath\VectorLock",
    "$modulesPath\Conductor", "$modulesPath\Historian", "$modulesPath\FractalLOD",
    "$modulesPath\RealmDivider", "$modulesPath\PulseProxy")

foreach ($f in $folders) { New-Item -ItemType Directory -Path $f -Force | Out-Null }

# 3. Компилятор C#
$cscPath = "C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
if (-not (Test-Path $cscPath)) {
    Write-Host "❌ C# компилятор не найден. Установите .NET Framework SDK" -ForegroundColor Red
    exit 1
}

# 4. Функция сохранения и компиляции модуля
function Add-Module {
    param($name, $content)
    
    $csPath = "$modulesPath\$name\$name.cs"
    $dllPath = "$binPath\$name.dll"
    
    $content | Out-File -FilePath $csPath -Encoding UTF8
    Write-Host "  📝 $name.cs создан" -ForegroundColor Gray
    
    & $cscPath /target:library /out:$dllPath $csPath
    if (Test-Path $dllPath) {
        Write-Host "  ✅ $name.dll скомпилирован" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Ошибка компиляции $name" -ForegroundColor Red
    }
}

# 5. TickGenerator
Add-Module -name "TickGenerator" -content @"
using System;
using System.Timers;

namespace SpectraVortex
{
    public class TickGenerator : IDisposable
    {
        private Timer _timer;
        private long _tick;
        private object _lock = new object();
        
        public event EventHandler<long> Tick;
        public double Frequency { get; private set; }
        public long CurrentTick => _tick;
        public bool IsRunning { get; private set; }
        
        public TickGenerator(double frequencyHz = 60.0)
        {
            Frequency = frequencyHz;
            _timer = new Timer(1000.0 / frequencyHz);
            _timer.Elapsed += (s, e) => {
                lock(_lock) {
                    _tick++;
                    Tick?.Invoke(this, _tick);
                }
            };
        }
        
        public void Start() { _timer.Start(); IsRunning = true; }
        public void Stop() { _timer.Stop(); IsRunning = false; }
        public void Dispose() { _timer?.Dispose(); }
    }
}
"@

# 6. TraceBuffer
Add-Module -name "TraceBuffer" -content @"
using System;
using System.Collections.Generic;

namespace SpectraVortex
{
    public class TraceBuffer
    {
        private Queue<TraceRecord> _records = new Queue<TraceRecord>();
        private int _maxSize;
        
        public TraceBuffer(int maxSize = 10000) { _maxSize = maxSize; }
        
        public void Push(string source, string type, double value, long tick)
        {
            lock(_records) {
                _records.Enqueue(new TraceRecord {
                    Timestamp = DateTime.UtcNow,
                    Source = source,
                    Type = type,
                    Value = value,
                    Tick = tick
                });
                while (_records.Count > _maxSize) _records.Dequeue();
            }
        }
        
        public IEnumerable<TraceRecord> GetRecent(int count)
        {
            lock(_records) {
                var result = new List<TraceRecord>();
                var arr = _records.ToArray();
                for (int i = Math.Max(0, arr.Length - count); i < arr.Length; i++)
                    result.Add(arr[i]);
                return result;
            }
        }
    }
    
    public class TraceRecord
    {
        public DateTime Timestamp { get; set; }
        public string Source { get; set; }
        public string Type { get; set; }
        public double Value { get; set; }
        public long Tick { get; set; }
    }
}
"@

# 7. VectorLock
Add-Module -name "VectorLock" -content @"
using System;

namespace SpectraVortex
{
    public class VectorLock
    {
        private string[] _order;
        private int _currentIndex = 0;
        private object _lock = new object();
        
        public event EventHandler<VectorLostEventArgs> VectorLost;
        public string CurrentHolder => _order?[_currentIndex];
        
        public void SetOrder(string[] order) { lock(_lock) { _order = order; _currentIndex = 0; } }
        
        public bool TryLock(string moduleName)
        {
            lock(_lock) {
                if (_order == null || _currentIndex >= _order.Length) return false;
                if (_order[_currentIndex] == moduleName) return true;
                return false;
            }
        }
        
        public void ReportLoss(string moduleName)
        {
            lock(_lock) {
                if (_order == null) return;
                if (_currentIndex < _order.Length && _order[_currentIndex] == moduleName)
                {
                    _currentIndex++;
                    string next = _currentIndex < _order.Length ? _order[_currentIndex] : null;
                    VectorLost?.Invoke(this, new VectorLostEventArgs(moduleName, next));
                }
            }
        }
    }
    
    public class VectorLostEventArgs : EventArgs
    {
        public string Lost { get; set; }
        public string Next { get; set; }
        public VectorLostEventArgs(string lost, string next) { Lost = lost; Next = next; }
    }
}
"@

# 8. Conductor
Add-Module -name "Conductor" -content @"
using System;

namespace SpectraVortex
{
    public class Conductor
    {
        private TickGenerator _tick;
        private TraceBuffer _trace;
        private VectorLock _lock;
        private double _vector = 0.5;
        
        public event EventHandler<double> VectorChanged;
        public double CurrentVector => _vector;
        
        public Conductor(TickGenerator tick, TraceBuffer trace, VectorLock vlock)
        {
            _tick = tick; _trace = trace; _lock = vlock;
            _tick.Tick += OnTick;
        }
        
        private void OnTick(object sender, long tickNum)
        {
            if (!_lock.TryLock("Conductor")) return;
            
            double newVector = Math.Sin(tickNum / 100.0) * 0.5 + 0.5;
            if (Math.Abs(newVector - _vector) > 0.01)
            {
                _vector = newVector;
                VectorChanged?.Invoke(this, _vector);
                _trace.Push("Conductor", "vector", _vector, tickNum);
            }
        }
    }
}
"@

# 9. Historian
Add-Module -name "Historian" -content @"
using System;
using System.Collections.Generic;

namespace SpectraVortex
{
    public class Historian
    {
        private TraceBuffer _trace;
        private List<CrisisEvent> _crises = new List<CrisisEvent>();
        
        public Historian(TraceBuffer trace) { _trace = trace; }
        
        public void EnterCrisis(string reason, double vectorBefore, long tick)
        {
            _crises.Add(new CrisisEvent {
                EnterTick = tick,
                EnterTime = DateTime.UtcNow,
                Reason = reason,
                VectorBefore = vectorBefore
            });
            _trace.Push("Historian", "crisis_enter", vectorBefore, tick);
        }
        
        public void ExitCrisis(double vectorAfter, long tick)
        {
            if (_crises.Count == 0) return;
            var last = _crises[_crises.Count - 1];
            last.ExitTick = tick;
            last.ExitTime = DateTime.UtcNow;
            last.VectorAfter = vectorAfter;
            last.VectorHeld = Math.Abs(vectorAfter - last.VectorBefore) < 0.1;
            _trace.Push("Historian", last.VectorHeld ? "crisis_passed" : "crisis_failed", vectorAfter, tick);
        }
    }
    
    public class CrisisEvent
    {
        public long EnterTick { get; set; }
        public long ExitTick { get; set; }
        public DateTime EnterTime { get; set; }
        public DateTime ExitTime { get; set; }
        public string Reason { get; set; }
        public double VectorBefore { get; set; }
        public double VectorAfter { get; set; }
        public bool VectorHeld { get; set; }
    }
}
"@

# 10. FractalLOD
Add-Module -name "FractalLOD" -content @"
using System;
using System.Collections.Generic;

namespace SpectraVortex
{
    public class FractalLOD
    {
        public class Cluster
        {
            public double Mass { get; set; }
            public double Vector { get; set; }
            public int Count { get; set; }
            public double Energy => Mass * Vector;
        }
        
        public Cluster Fold(List<double> masses, List<double> vectors)
        {
            var c = new Cluster();
            for (int i = 0; i < masses.Count && i < vectors.Count; i++)
            {
                c.Mass += masses[i];
                c.Vector += vectors[i];
                c.Count++;
            }
            if (c.Count > 0) c.Vector /= c.Count;
            return c;
        }
    }
}
"@

# 11. RealmDivider
Add-Module -name "RealmDivider" -content @"
using System;

namespace SpectraVortex
{
    public class RealmDivider
    {
        private VectorLock _lock;
        private TraceBuffer _trace;
        private TickGenerator _tick;
        private object _lastSnapshot;
        private long _snapshotTick;
        
        public RealmDivider(VectorLock vlock, TraceBuffer trace, TickGenerator tick)
        {
            _lock = vlock; _trace = trace; _tick = tick;
            _lock.VectorLost += OnVectorLost;
        }
        
        public void SaveSnapshot(object state, long tick)
        {
            _lastSnapshot = state;
            _snapshotTick = tick;
            _trace.Push("RealmDivider", "snapshot", 1.0, tick);
        }
        
        private void OnVectorLost(object sender, VectorLostEventArgs e)
        {
            _trace.Push("RealmDivider", "vector_lost", _tick.CurrentTick, _tick.CurrentTick);
            if (e.Next == null && _lastSnapshot != null)
            {
                _trace.Push("RealmDivider", "emergency_division", _snapshotTick, _tick.CurrentTick);
                // Здесь будет восстановление из снапшота
            }
        }
    }
}
"@

# 12. PulseProxy (коммерческий)
Add-Module -name "PulseProxy" -content @"
using System;
using System.Collections.Generic;

namespace SpectraVortex.Commercial
{
    public class PulseProxy
    {
        private TickGenerator _tick;
        private TraceBuffer _trace;
        private Queue<double> _externalFreq = new Queue<double>();
        
        public event EventHandler<double> PulsePredicted;
        public bool Synchronized { get; private set; }
        
        public PulseProxy(TickGenerator tick, TraceBuffer trace)
        {
            _tick = tick; _trace = trace;
        }
        
        public void Feed(double freq)
        {
            lock(_externalFreq)
            {
                _externalFreq.Enqueue(freq);
                while (_externalFreq.Count > 50) _externalFreq.Dequeue();
                
                if (_externalFreq.Count >= 10)
                {
                    double sum = 0;
                    foreach (var f in _externalFreq) sum += f;
                    double avg = sum / _externalFreq.Count;
                    
                    Synchronized = Math.Abs(avg - _tick.Frequency) < (_tick.Frequency * 0.05);
                    _trace.Push("PulseProxy", "sync", Synchronized ? 1.0 : 0.0, _tick.CurrentTick);
                    
                    if (Synchronized) PulsePredicted?.Invoke(this, avg);
                }
            }
        }
        
        public double? NextPulseMs()
        {
            if (!Synchronized || _externalFreq.Count < 10) return null;
            return 1000.0 / (_tick.Frequency);
        }
    }
}
"@

# 13. Python-ядро rizoma_core.py
$corePy = @"
# rizoma_core.py
# Единое ядро Ризомы (Python + C#)
import clr
import sys
import os
from pathlib import Path
import threading
import json
from datetime import datetime

# Добавляем путь к DLL
bin_path = r"C:\Program Files\SpectraVortex\Bin"
sys.path.append(bin_path)

# Загружаем сборки
clr.AddReference("TickGenerator")
clr.AddReference("TraceBuffer")
clr.AddReference("VectorLock")
clr.AddReference("Conductor")
clr.AddReference("Historian")
clr.AddReference("FractalLOD")
clr.AddReference("RealmDivider")
clr.AddReference("PulseProxy")

from SpectraVortex import *
from SpectraVortex.Commercial import PulseProxy

class RizomaCore:
    """Единое ядро Ризомы"""
    
    def __init__(self, frequency=60.0):
        # Создаём модули
        self.tick = TickGenerator(frequency)
        self.trace = TraceBuffer(10000)
        self.vlock = VectorLock()
        self.conductor = Conductor(self.tick, self.trace, self.vlock)
        self.historian = Historian(self.trace)
        self.fractal = FractalLOD()
        self.divider = RealmDivider(self.vlock, self.trace, self.tick)
        self.pulse = PulseProxy(self.tick, self.trace)
        
        # Порядок наследования
        self.vlock.SetOrder(["Conductor", "PulseProxy", "Historian"])
        
        # Фоновый поток для такта
        self._running = False
        self._thread = None
        
        # Подписка на события
        def on_tick(sender, tick):
            if tick % 1000 == 0:
                print(f"⚡ Такт #{tick}")
        
        self.tick.Tick += on_tick
        
    def start(self):
        """Запуск системы"""
        self._running = True
        self.tick.Start()
        print("✅ Ризома запущена")
        
    def stop(self):
        """Остановка системы"""
        self._running = False
        self.tick.Stop()
        print("⏹️ Ризома остановлена")
        
    def feed_external(self, frequency):
        """Подать внешний сигнал в PulseProxy"""
        self.pulse.Feed(frequency)
        
    def get_status(self):
        """Текущее состояние"""
        return {
            "tick": self.tick.CurrentTick,
            "frequency": self.tick.Frequency,
            "vector": self.conductor.CurrentVector,
            "sync": self.pulse.Synchronized,
            "next_pulse_ms": self.pulse.NextPulseMs()
        }
        
    def save_snapshot(self, state):
        """Сохранить снапшот"""
        self.divider.SaveSnapshot(state, self.tick.CurrentTick)
        
    def trace_recent(self, count=10):
        """Последние следы"""
        return list(self.trace.GetRecent(count))

# Глобальный экземпляр (для декораторов)
_core = None

def init_core(frequency=60.0):
    """Инициализация ядра (вызвать один раз)"""
    global _core
    if _core is None:
        _core = RizomaCore(frequency)
    return _core

def get_core():
    """Получить текущее ядро"""
    return _core

# Декораторы для старых модулей
def synchronized(func):
    """Декоратор: функция выполняется в такте"""
    def wrapper(*args, **kwargs):
        core = get_core()
        if core and core.tick.IsRunning:
            tick_before = core.tick.CurrentTick
            result = func(*args, **kwargs)
            core.trace.Push(func.__name__, "exec", 1.0, core.tick.CurrentTick)
            return result
        else:
            return func(*args, **kwargs)
    return wrapper

def traced(trace_type="info"):
    """Декоратор: запись следа"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            core = get_core()
            result = func(*args, **kwargs)
            if core:
                core.trace.Push(func.__name__, trace_type, 1.0, core.tick.CurrentTick)
            return result
        return wrapper
    return decorator

def vector_aware(func):
    """Декоратор: учёт текущего вектора"""
    def wrapper(*args, **kwargs):
        core = get_core()
        if core:
            kwargs['current_vector'] = core.conductor.CurrentVector
        return func(*args, **kwargs)
    return wrapper
"@

$corePy | Out-File -FilePath "$corePath\rizoma_core.py" -Encoding UTF8
Write-Host "✅ Python-ядро создано: $corePath\rizoma_core.py" -ForegroundColor Green

# 14. Конфигурация
$config = @"
{
    "version": "2.0.0",
    "frequency": 60.0,
    "order": ["Conductor", "PulseProxy", "Historian"],
    "legacy": {
        "rhizome_v2": true,
        "rhizome_infinite": true,
        "rhizome_real_pulse": true,
        "rhizome_spotters": true,
        "resonance_gravitsapa": true
    },
    "paths": {
        "logs": "C:\\ProgramData\\SpectraVortex\\Logs",
        "data": "C:\\Users\\Dim\\spectravortex\\commercial\\data"
    }
}
"@

$config | Out-File -FilePath "$configPath\rizoma.json" -Encoding UTF8
Write-Host "✅ Конфигурация создана" -ForegroundColor Green

# 15. Тестовый скрипт
$testPy = @"
# test_rizoma_core.py
import sys
sys.path.append(r"C:\Program Files\SpectraVortex\Core")
from rizoma_core import init_core, get_core
import time

print("🧪 ТЕСТ ЕДИНОГО ЯДРА РИЗОМЫ")
core = init_core(10.0)  # 10 Гц для наглядности
core.start()

# Подаём внешний сигнал
for i in range(20):
    core.feed_external(9.8 + (i % 5) * 0.1)
    time.sleep(0.2)

time.sleep(2)

print("\n📊 Статус:")
status = core.get_status()
for k, v in status.items():
    print(f"  {k}: {v}")

print("\n📝 Последние следы:")
for t in core.trace_recent(5):
    print(f"  {t.Timestamp}: {t.Source} - {t.Type} = {t.Value:.3f}")

core.stop()
print("✅ Тест завершён")
"@

$testPy | Out-File -FilePath "$corePath\test_rizoma_core.py" -Encoding UTF8
Write-Host "✅ Тестовый скрипт создан" -ForegroundColor Green

# 16. Финальное сообщение
Write-Host @"

╔════════════════════════════════════════════════════════════════╗
║  🎯 ЕДИНАЯ СБОРКА РИЗОМЫ ЗАВЕРШЕНА                             ║
║  Принцип: не чиним 96% - достраиваем                          ║
╠════════════════════════════════════════════════════════════════╣
║  📍 Модули (DLL): C:\Program Files\SpectraVortex\Bin\        ║
║  🐍 Python-ядро:  C:\Program Files\SpectraVortex\Core\rizoma_core.py ║
║  ⚙️ Конфиг:       C:\ProgramData\SpectraVortex\Config\rizoma.json ║
║  📊 Логи:         C:\ProgramData\SpectraVortex\Logs\         ║
║  🧪 Тест:         C:\Program Files\SpectraVortex\Core\test_rizoma_core.py ║
╠════════════════════════════════════════════════════════════════╣
║  ▶️ Для теста запустите:                                       ║
║     python "C:\Program Files\SpectraVortex\Core\test_rizoma_core.py" ║
║                                                                ║
║  ▶️ Интеграция со старыми модулями:                            ║
║     from rizoma_core import init_core, synchronized, traced  ║
╚════════════════════════════════════════════════════════════════╝

Фаза: сборка. Вектор: удержан. 96% - сохранены. Скелет - готов.
"@ -ForegroundColor Magenta