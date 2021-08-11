namespace TrProtocol.Packets
{
    public class FishOutNPC : Packet
    {
        public override MessageID Type => MessageID.FinishedConnectingToServer;
        public ushort X { get; set; }
        public ushort Y { get; set; }
        public short Start { get; set; }
    }
}