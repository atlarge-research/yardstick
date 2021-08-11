namespace TrProtocol.Packets
{
    public class TamperWithNPC : Packet, INPCSlot, IOtherPlayerSlot
    {
        public override MessageID Type => MessageID.TamperWithNPC;
        public short NPCSlot { get; set; }
        public byte UniqueImmune { get; set; }
        [Condition("UniqueImmune", 1L)]
        public int Time { get; set; }
        [Condition("UniqueImmune", 1L)]
        public byte OtherPlayerSlot { get; set; }
        public byte HighBitOfPlayerIsAlwaysZero { get; set; } = 0;
    }
}