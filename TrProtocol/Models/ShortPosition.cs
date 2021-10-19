namespace TrProtocol.Models
{
    public partial struct ShortPosition
    {
        public short X, Y;
        public override string ToString()
        {
            return $"[{X}, {Y}]";
        }
    }
}
