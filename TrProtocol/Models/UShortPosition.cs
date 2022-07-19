using System.Runtime.InteropServices;

namespace TrProtocol.Models;

[StructLayout(LayoutKind.Sequential)]
public partial struct UShortPosition
{
    public ushort X;
    public ushort Y;
}
