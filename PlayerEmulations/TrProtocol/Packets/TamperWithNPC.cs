namespace TrProtocol.Packets;

public class TamperWithNPC : Packet, INPCSlot, IOtherPlayerSlot
{
    public override MessageID Type => MessageID.TamperWithNPC;
    public short NPCSlot { get; set; }
    public byte UniqueImmune { get; set; }
    private bool _isUniqueImmune => UniqueImmune == 1;

    [Condition(nameof(_isUniqueImmune))]
    public int Time { get; set; }
    [Condition(nameof(_isUniqueImmune))]
    public byte OtherPlayerSlot { get; set; }
    public byte HighBitOfPlayerIsAlwaysZero { get; set; } = 0;
}