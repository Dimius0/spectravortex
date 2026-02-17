# install_rizoma_full_ascii.ps1
# Full Rizoma installation (8 modules)

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  FULL RIZOMA INSTALLATION (8 MODULES)  " -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta

# Admin check
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { 
    Write-Host "ERROR: Run as administrator" -ForegroundColor Red
    exit 1 
}

# dotnet check
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) { 
    Write-Host "ERROR: dotnet not found" -ForegroundColor Red
    exit 1 
}
Write-Host "dotnet: $(dotnet --version)" -ForegroundColor Cyan

# Directories
$basePath = "C:\Program Files\SpectraVortex"
$modulesPath = "$basePath\Modules"
$binPath = "$basePath\Bin"
$corePath = "$basePath\Core"
$projPath = "$basePath\Project"

@($basePath, $modulesPath, $binPath, $corePath, $projPath) | ForEach-Object { 
    New-Item -ItemType Directory -Path $_ -Force | Out-Null 
}

# 1. TickGenerator
@"
using System;
using System.Threading;

namespace SpectraVortex
{
    public class TickGenerator
    {
        private long _tick;
        private object _lock = new object();
        private volatile bool _running;
        private Thread _thread;
        private int _delayMs;
        
        public event EventHandler<long> Tick;
        public double Frequency { get; private set; }
        public long CurrentTick { get { lock(_lock) { return _tick; } } }
        public bool IsRunning { get { return _running; } }
        
        public TickGenerator(double frequencyHz = 60.0)
        {
            Frequency = frequencyHz;
            _delayMs = (int)(1000.0 / frequencyHz);
            if (_delayMs < 1) _delayMs = 1;
            _tick = 0;
            _running = false;
        }
        
        public void Start() { if (_running) return; _running = true; _thread = new Thread(Run); _thread.IsBackground = true; _thread.Start(); }
        public void Stop() { _running = false; _thread?.Join(2000); }
        
        private void Run()
        {
            while (_running) { Thread.Sleep(_delayMs); lock(_lock) { _tick++; Tick?.Invoke(this, _tick); } }
        }
    }
}
"@ | Out-File -FilePath "$modulesPath\TickGenerator.cs" -Encoding ASCII

# 2. TraceBuffer
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
"@ | Out-File -FilePath "$modulesPath\TraceBuffer.cs" -Encoding ASCII

# 3. VectorLock
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
        public bool TryLock(string moduleName) { lock(_lock) { if (_order == null || _currentIndex >= _order.Length) return false; return _order[_currentIndex] == moduleName; } }
        
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
"@ | Out-File -FilePath "$modulesPath\VectorLock.cs" -Encoding ASCII

# 4. Conductor
@"
using System;

namespace SpectraVortex
{
    public class Conductor
    {
        private TickGenerator _tick;
        private TraceBuffer _trace;
        private VectorLock _vlock;
        private double _vector = 0.5;
        
        public event EventHandler<double> VectorChanged;
        public double CurrentVector { get { return _vector; } }
        
        public Conductor(TickGenerator tick, TraceBuffer trace, VectorLock vlock)
        {
            _tick = tick; _trace = trace; _vlock = vlock;
            _tick.Tick += OnTick;
        }
        
        private void OnTick(object sender, long tickNum)
        {
            if (!_vlock.TryLock("Conductor")) return;
            
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
"@ | Out-File -FilePath "$modulesPath\Conductor.cs" -Encoding ASCII

# 5. Historian
@"
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
"@ | Out-File -FilePath "$modulesPath\Historian.cs" -Encoding ASCII

# 6. FractalLOD
@"
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
            public double Energy { get { return Mass * Vector; } }
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
"@ | Out-File -FilePath "$modulesPath\FractalLOD.cs" -Encoding ASCII

# 7. RealmDivider
@"
using System;

namespace SpectraVortex
{
    public class RealmDivider
    {
        private VectorLock _vlock;
        private TraceBuffer _trace;
        private TickGenerator _tick;
        private object _lastSnapshot;
        private long _snapshotTick;
        
        public RealmDivider(VectorLock vlock, TraceBuffer trace, TickGenerator tick)
        {
            _vlock = vlock; _trace = trace; _tick = tick;
            _vlock.VectorLost += OnVectorLost;
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
            }
        }
    }
}
"@ | Out-File -FilePath "$modulesPath\RealmDivider.cs" -Encoding ASCII

# 8. PulseProxy (commercial)
@"
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
            return 1000.0 / _tick.Frequency;
        }
    }
}
"@ | Out-File -FilePath "$modulesPath\PulseProxy.cs" -Encoding ASCII

# Create project file
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
"@ | Out-File -FilePath "$projPath\RizomaModules.csproj" -Encoding ASCII

# Compile
Write-Host "Compiling 8 modules..." -ForegroundColor Yellow
dotnet build "$projPath\RizomaModules.csproj" -c Release -o $binPath --force

if ($LASTEXITCODE -ne 0) { 
    Write-Host "Build failed" -ForegroundColor Red
    exit 1 
}

# Python core
@"
import clr
import sys
import time
import threading

clr.AddReference("System")
clr.AddReference("System.Collections")
clr.AddReference("System.Threading")

sys.path.append(r"C:\Program Files\SpectraVortex\Bin")
clr.AddReference("RizomaModules")

from SpectraVortex import *
from SpectraVortex.Commercial import PulseProxy

class RizomaCore:
    def __init__(self, freq=60.0):
        print("Initializing core (8 modules)")
        self.tick = TickGenerator(freq)
        self.trace = TraceBuffer(10000)
        self.vlock = VectorLock()
        self.vlock.SetOrder(["Conductor", "PulseProxy", "Historian"])
        self.conductor = Conductor(self.tick, self.trace, self.vlock)
        self.historian = Historian(self.trace)
        self.fractal = FractalLOD()
        self.divider = RealmDivider(self.vlock, self.trace, self.tick)
        self.pulse = PulseProxy(self.tick, self.trace)
        self.running = False
        
    def start(self):
        self.tick.Start()
        self.running = True
        print("Rizoma started (8 modules)")
        
    def stop(self):
        self.tick.Stop()
        self.running = False
        print("Rizoma stopped")
        
    def get_tick(self):
        return self.tick.CurrentTick
        
    def feed_pulse(self, freq):
        self.pulse.Feed(freq)
        
    def get_status(self):
        return {
            "tick": self.get_tick(),
            "running": self.running,
            "vector": self.conductor.CurrentVector,
            "sync": self.pulse.Synchronized,
            "holder": self.vlock.CurrentHolder
        }

_core_instance = None

def init_core(freq=60.0):
    global _core_instance
    if _core_instance is None:
        _core_instance = RizomaCore(freq)
    return _core_instance

def get_core():
    return _core_instance
"@ | Out-File -FilePath "$corePath\rizoma_core.py" -Encoding ASCII

# Test script
@"
import sys
import time
sys.path.append(r"C:\Program Files\SpectraVortex\Core")
from rizoma_core import init_core

core = init_core(10.0)
core.start()

print("Testing 8 modules (5 seconds)...")
for i in range(5):
    time.sleep(1)
    core.feed_pulse(9.8 + i*0.1)
    status = core.get_status()
    print(f"   Sec {i+1}: tick={status['tick']}, vector={status['vector']:.3f}, sync={status['sync']}")

core.stop()
print(f"Final tick: {core.get_tick()}")
"@ | Out-File -FilePath "$corePath\test_full.py" -Encoding ASCII

Write-Host @"
========================================
  FULL INSTALLATION COMPLETE (8 MODULES)
  Core: $corePath\rizoma_core.py
  Test: $corePath\test_full.py
  DLL:  $binPath\RizomaModules.dll
========================================
  Run test: python "$corePath\test_full.py"
========================================
"@ -ForegroundColor Cyan