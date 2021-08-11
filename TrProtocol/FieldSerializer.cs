using System.IO;

namespace TrProtocol
{
    public abstract class FieldSerializer<T> : IFieldSerializer
    {
        protected abstract T _Read(BinaryReader br);

        protected abstract void _Write(BinaryWriter bw, T t);

        public object Read(BinaryReader br)
        {
            return _Read(br);
        }

        public void Write(BinaryWriter bw, object o)
        {
            _Write(bw, (T)o);
        }
    }
}
