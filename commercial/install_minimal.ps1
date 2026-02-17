# install_minimal.ps1
Write-Host "🚀 Минимальная установка Ризомы" -ForegroundColor Green

# Проверка админа
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { Write-Host "❌ Запустите от имени администратора" -ForegroundColor Red; exit 1 }

# Проверка dotnet
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) { Write-Host "❌ dotnet не найден" -ForegroundColor Red; exit 1 }
Write-Host "✅ dotnet: $(dotnet --version)" -ForegroundColor Cyan

# Директории
$basePath = "C:\Program Files\SpectraVortex"
$modulesPath = "$basePath\Modules"
$binPath = "$basePath\Bin"
$corePath = "$basePath\Core"
$projPath = "$basePath\Project"

@($basePath, $modulesPath, $binPath, $corePath, $projPath) | ForEach-Object { New-Item -ItemType Directory -Path $_ -Force | Out-Null }

# TickGenerator.cs
@"
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
        
        public TickGenerator(double frequencyHz = 60.0)
        {
            Frequency = frequencyHz;
            _timer = new Timer(1000.0 / frequencyHz);
            _timer.Elapsed += (s, e) => {
                lock(_lock) { _tick++; Tick?.Invoke(this, _tick); }
            };
        }
        
        public void Start() { _timer.Start(); }
        public void Stop() { _timer.Stop(); }
        public void Dispose() { _timer?.Dispose(); }
    }
}
"@ | Out-File -FilePath "$modulesPath\TickGenerator.cs" -Encoding UTF8

# TraceBuffer.cs
@"
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
"@ | Out-File -FilePath "$modulesPath\TraceBuffer.cs" -Encoding UTF8

# VectorLock.cs
@"
using System;

namespace SpectraVortex
{
    public class VectorLock
    {
        private string[] _order;
        private int _currentIndex = 0;
        private object _lock = new object();
        
        public event EventHandler<VectorLostEventArgs> VectorLost;
        public string CurrentHolder { get { lock(_lock) { return _order?[_currentIndex]; } } }
        
        public void SetOrder(string[] order) { lock(_lock) { _order = order; _currentIndex = 0; } }
        
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
"@ | Out-File -FilePath "$modulesPath\VectorLock.cs" -Encoding UTF8

# Создаём проект
@"
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <OutputType>Library</OutputType>
  </PropertyGroup>
  <ItemGroup>
    <Compile Include="..\Modules\*.cs" />
  </ItemGroup>
</Project>
"@ | Out-File -FilePath "$projPath\RizomaModules.csproj" -Encoding UTF8

# Компиляция
Write-Host "🔨 Компиляция..." -ForegroundColor Yellow
dotnet build "$projPath\RizomaModules.csproj" -c Release -o $binPath
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Ошибка сборки" -ForegroundColor Red; exit 1 }

# Python-ядро (отдельным файлом)
@"
import clr
import sys
sys.path.append(r"C:\Program Files\SpectraVortex\Bin")
clr.AddReference("RizomaModules")
from SpectraVortex import *

class RizomaCore:
    def __init__(self, freq=60.0):
        self.tick = TickGenerator(freq)
        self.trace = TraceBuffer(10000)
        self.vlock = VectorLock()
        self.vlock.SetOrder(["TickGenerator"])
        
    def start(self): self.tick.Start()
    def stop(self): self.tick.Stop()
    def get_tick(self): return self.tick.CurrentTick

def init_core(freq=60.0):
    global _core
    if '_core' not in globals():
        _core = RizomaCore(freq)
    return _core
"@ | Out-File -FilePath "$corePath\rizoma_core.py" -Encoding UTF8

# Тест
@"
import sys
sys.path.append(r"C:\Program Files\SpectraVortex\Core")
from rizoma_core import init_core
import time

core = init_core(10.0)
core.start()
print('⚡ 3 секунды...')
for i in range(3):
    time.sleep(1)
    print(f'   Такт: {core.get_tick()}')
core.stop()
print(f'✅ Итог: {core.get_tick()}')
"@ | Out-File -FilePath "$corePath\test.py" -Encoding UTF8

Write-Host @"

✅ УСТАНОВКА ЗАВЕРШЕНА
📍 Python: $corePath\rizoma_core.py
📍 Тест: $corePath\test.py
📍 DLL: $binPath\RizomaModules.dll

▶️ Запусти тест: python "$corePath\test.py"
"@ -ForegroundColor Cyan