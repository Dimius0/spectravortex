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
