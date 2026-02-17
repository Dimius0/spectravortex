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
