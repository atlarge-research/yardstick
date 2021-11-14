namespace TrProtocol.Models
{
    public partial struct ShortPosition
    {
        public ShortPosition(short x, short y)
        {
            X = x;
            Y = y;
        }
        public short X, Y;
        public override string ToString()
        {
            return $"[{X}, {Y}]";
        }
    }
}
