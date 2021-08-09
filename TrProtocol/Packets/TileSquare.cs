namespace TrProtocol.Packets
{
    public class TileSquare : Packet
    {
        public override MessageID Type => MessageID.TileSquare;
        public byte[] Data { get; set; }
    }
}
