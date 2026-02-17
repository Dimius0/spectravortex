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
