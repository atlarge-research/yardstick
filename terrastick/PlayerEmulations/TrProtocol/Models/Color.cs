using System.Runtime.InteropServices;

namespace TrProtocol.Models;

[StructLayout(LayoutKind.Sequential)]
public partial struct Color
{
    public int R;
    public int G;
    public int B;
    public Color(byte r, byte g, byte b)
    {
        R = r;
        G = g;
        B = b;
    }

    public static readonly Color White = new(0xFF, 0xFF, 0xFF);
}
