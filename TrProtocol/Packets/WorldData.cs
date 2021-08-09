namespace TrProtocol.Packets
{
    public class WorldData : Packet
    {
        public override MessageID Type => MessageID.WorldData;
        public byte[] Data { get; set; }
    }
}
