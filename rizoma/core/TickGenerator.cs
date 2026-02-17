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
