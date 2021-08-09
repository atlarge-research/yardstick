namespace TrProtocol.Packets
{
    public class TileSection : Packet
    {
        public override MessageID Type => MessageID.TileSection;
        public byte[] Data { get; set; }
    }
}
