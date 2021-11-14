using System;
using System.IO;
using System.Reflection;

namespace TrProtocol
{
    public interface IFieldSerializer
    {
        protected static object[] empty = Array.Empty<object>();
        object Read(BinaryReader br);
        void Write(BinaryWriter bw, object o);
    }

    public interface IConfigurable
    {
        IFieldSerializer Configure(PropertyInfo prop, string version);
    }
}
