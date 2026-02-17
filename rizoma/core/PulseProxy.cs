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
                    
                    // ???????? ??????? ??? Math.Abs
                    double diff = avg - _tick.Frequency;
                    if (diff < 0) diff = -diff;
                    
                    Synchronized = diff < (_tick.Frequency * 0.05);
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
