using System.IO;

namespace TrProtocol
{
    public interface ISerializer
    {
        object Read(BinaryReader br);
        void Write(BinaryWriter bw, object o);
    }
}
