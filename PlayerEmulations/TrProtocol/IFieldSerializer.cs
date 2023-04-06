using System.Reflection;

namespace TrProtocol;

public interface IFieldSerializer
{
    object Read(BinaryReader br);
    void Write(BinaryWriter bw, object o);
}

public interface IConfigurable
{
    IConfigurable Configure(PropertyInfo prop, string version);
}
