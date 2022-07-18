using System.Runtime.InteropServices;

namespace TrProtocol.Models;

[StructLayout(LayoutKind.Sequential)]
public partial struct Position
{
    public Position(int x, int y)
    {
        X = x;
        Y = y;
    }
    public int X, Y;
    public override string ToString()
    {
        return $"[{X}, {Y}]";
    }
}
