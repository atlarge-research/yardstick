namespace TrProtocol.Packets
{
    public class TamperWithNPC : Packet, INPCSlot, IOtherPlayerSlot
    {
        public override MessageID Type => MessageID.TamperWithNPC;
        public short NPCSlot { get; set; }
        public byte UniqueImmune { get; set; }
        [Ignore] public bool IsUniqueImmune => UniqueImmune == 1;

        [Condition("IsUniqueImmune")]
        public int Time { get; set; }
        [Condition("IsUniqueImmune")]
        public byte OtherPlayerSlot { get; set; }
        public byte HighBitOfPlayerIsAlwaysZero { get; set; } = 0;
    }
}