namespace TrProtocol.Models
{
    // Token: 0x02000854 RID: 2132
    public partial struct Color
    {
        public int R, G, B;
        public Color(byte r, byte g, byte b)
        {
            R = r;
            G = g;
            B = b;
        }

        public static Color White = new Color(0xff, 0xff, 0xff);
    }
}
