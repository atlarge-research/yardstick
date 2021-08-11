using System.IO;

namespace TrProtocol
{
    public interface IFieldSerializer
    {
        object Read(BinaryReader br);
        void Write(BinaryWriter bw, object o);
    }
}
