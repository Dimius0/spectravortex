# install_rizoma_dotnet.ps1
# Установка Ризомы через dotnet build

Write-Host "🚀 Установка Ризомы (dotnet build)" -ForegroundColor Green

# Проверка админа
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ Запустите от имени администратора" -ForegroundColor Red
    exit 1
}

# Проверка dotnet
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    Write-Host "❌ dotnet не найден. Установите .NET SDK 8+" -ForegroundColor Red
    exit 1
}

Write-Host "✅ dotnet версия: $(dotnet --version)" -ForegroundColor Cyan

# Директории
$basePath = "C:\Program Files\SpectraVortex"
$modulesPath = "$basePath\Modules"
$binPath = "$basePath\Bin"
$configPath = "C:\ProgramData\SpectraVortex\Config"
$logPath = "C:\ProgramData\SpectraVortex\Logs"
$corePath = "$basePath\Core"
$projPath = "$basePath\Project"

# Создаём папки
@($basePath, $modulesPath, $binPath, $configPath, $logPath, $corePath, $projPath) | ForEach-Object {
    New-Item -ItemType Directory -Path $_ -Force | Out-Null
}

# Создаём .cs файлы модулей
$modules = @{
    "TickGenerator" = @'
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
        public long CurrentTick { get { lock(_lock) { return _tick; } } }
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
'@

    "TraceBuffer" = @'
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
        
        public TraceRecord[] GetRecent(int count)
        {
            lock(_records) {
                var arr = _records.ToArray();
                int start = Math.Max(0, arr.Length - count);
                int len = arr.Length - start;
                var result = new TraceRecord[len];
                Array.Copy(arr, start, result, 0, len);
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
'@

    "VectorLock" = @'
using System;

namespace SpectraVortex
{
    public class VectorLock
    {
        private string[] _order;
        private int _currentIndex = 0;
        private object _lock = new object();
        
        public event EventHandler<VectorLostEventArgs> VectorLost;
        public string CurrentHolder 
        { 
            get 
            { 
                lock(_lock) 
                { 
                    if (_order == null || _currentIndex >= _order.Length) return null;
                    return _order[_currentIndex]; 
                } 
            } 
        }
        
        public void SetOrder(string[] order) 
        { 
            lock(_lock) 
            { 
                _order = order; 
                _currentIndex = 0; 
            } 
        }
        
        public bool TryLock(string moduleName)
        {
            lock(_lock) {
                if (_order == null || _currentIndex >= _order.Length) return false;
                return _order[_currentIndex] == moduleName;
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
'@
}

# Сохраняем файлы
foreach ($name in $modules.Keys) {
    $path = "$modulesPath\$name.cs"
    $modules[$name] | Out-File -FilePath $path -Encoding UTF8
    Write-Host "  📝 $name.cs" -ForegroundColor Gray
}

# Создаём проект
$projContent = @'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <OutputType>Library</OutputType>
    <GenerateAssemblyInfo>false</GenerateAssemblyInfo>
  </PropertyGroup>
</Project>
'@
$projContent | Out-File -FilePath "$projPath\RizomaModules.csproj" -Encoding UTF8

# Копируем .cs файлы в папку проекта для компиляции
foreach ($name in $modules.Keys) {
    Copy-Item "$modulesPath\$name.cs" "$projPath\" -Force
}

# Сборка
Write-Host "🔨 Компиляция модулей..." -ForegroundColor Yellow
dotnet build "$projPath\RizomaModules.csproj" -c Release -o $binPath

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Сборка успешна" -ForegroundColor Green
} else {
    Write-Host "❌ Ошибка сборки" -ForegroundColor Red
    exit 1
}

# Python-ядро (экранировано)
$pyCode = @'
# rizoma_core.py
import clr
import sys
sys.path.append(r"C:\Program Files\SpectraVortex\Bin")

clr.AddReference("RizomaModules")
from SpectraVortex import TickGenerator, TraceBuffer, VectorLock

class RizomaCore:
    def __init__(self, freq=60.0):
        self.tick = TickGenerator(freq)
        self.trace = TraceBuffer(10000)
        self.vlock = VectorLock()
        self.vlock.SetOrder(["TickGenerator"])
        
    def start(self):
        self.tick.Start()
        print("✅ Ризома запущена")
        
    def stop(self):
        self.tick.Stop()
        print("⏹️ Ризома остановлена")
        
    def get_tick(self):
        return self.tick.CurrentTick

def init_core(freq=60.0):
    global _core
    if "_core" not in globals():
        _core = RizomaCore(freq)
    return _core
'@
$pyCode | Out-File -FilePath "$corePath\rizoma_core.py" -Encoding UTF8
Write-Host "  ✅ rizoma_core.py" -ForegroundColor Green

# Тест
$testCode = @'
# test.py
import sys
sys.path.append(r"C:\Program Files\SpectraVortex\Core")
from rizoma_core import init_core
import time

core = init_core(10.0)
core.start()
print("⚡ Наблюдаем 3 секунды...")
for i in range(3):
    time.sleep(1)
    print(f"   Такт: {core.get_tick()}")
core.stop()
print(f"✅ Итоговый такт: {core.get_tick()}")
'@

╔══════════════════════════════════════════════════════════════╗
║  ✅ УСТАНОВКА ЗАВЕРШЕНА                                      ║
║  📍 Python-ядро: $corePath\rizoma_core.py                   ║
║  📍 Тест:       $corePath\test.py                           ║
║  📍 DLL:        $binPath\RizomaModules.dll                  ║
╠══════════════════════════════════════════════════════════════╣
║  ▶️ Запусти тест:                                            ║
║     python "$corePath\test.py"                              ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan