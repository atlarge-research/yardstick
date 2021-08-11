namespace TrProtocol.Packets
{
    public class TileEntitySharing : Packet
    {
        public override MessageID Type => MessageID.TileEntitySharing;
        public int ID { get; set; }
        public bool IsNew { get; set; }
        [Condition("IsNew")] public byte[] TileEntityData { get; set; }
    }
}