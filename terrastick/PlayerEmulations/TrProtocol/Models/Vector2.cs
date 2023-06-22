using System.Runtime.InteropServices;

namespace TrProtocol.Models;

[StructLayout(LayoutKind.Sequential)]
public partial struct Vector2
{
    public Vector2(float x, float y)
    {
        X = x;
        Y = y;
    }

    public float X;
    public float Y;

    public override string ToString()
    {
        return $"[{X}, {Y}]";
    }
    public static Vector2 Lerp(Vector2 origin,Vector2 dest, float amount)
    {
        var X = origin.X + (dest.X - origin.X) * amount;
        var Y = origin.Y + (dest.Y - origin.Y) * amount;
        return new Vector2(X, Y);

    }
}
