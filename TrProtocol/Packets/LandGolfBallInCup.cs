namespace TrProtocol.Packets
{
    public class LandGolfBallInCup : Packet, IOtherPlayerSlot
    {
        public override MessageID Type => MessageID.LandGolfBallInCup;
        public byte OtherPlayerSlot { get; set; }
        public ushort X { get; set; }
        public ushort Y { get; set; }
        public ushort Hits { get; set; }
        public ushort ProjType { get; set; }
    }
}