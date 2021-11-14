using System;
using System.IO;
using System.Reflection;

namespace TrProtocol
{
    public abstract class NumFieldSerializer<T> : FieldSerializer<T>, IConfigurable
    {
        private int upper, lower;
        private T zero;
        private bool interrupt, enabled;
        public override void Write(BinaryWriter bw, object o)
        {
            if (enabled)
            {
                var o2 = Convert.ToInt32(o);
                if (o2 > upper || o2 < lower)
                {
                    if (interrupt)
                        throw new BadBoundException(
                            $"packet ignored due to field {typeof(T)} = {o2} outer bound ({lower}, {upper})");
                    o = zero;
                }
            }
            _Write(bw, (T)o);
        }

        public IFieldSerializer Configure(PropertyInfo prop, string version)
        {
            var instance = (NumFieldSerializer<T>) MemberwiseClone();
            foreach (var bound in prop.GetCustomAttributes<BoundAttribute>())
            {
                if (bound.version != version) continue; ;
                instance.zero = (T)Convert.ChangeType(0, prop.PropertyType);
                instance.upper = bound.upper;
                instance.lower = bound.lower;
                instance.interrupt = bound.interrupt;
                instance.enabled = true;
            }
            return instance;
        }
    }
    public abstract class FieldSerializer<T> : IFieldSerializer
    {
        protected abstract T _Read(BinaryReader br);

        protected abstract void _Write(BinaryWriter bw, T t);

        public virtual object Read(BinaryReader br)
        {
            return _Read(br);
        }

        public virtual void Write(BinaryWriter bw, object o)
        {
            _Write(bw, (T)o);
        }
    }
}
