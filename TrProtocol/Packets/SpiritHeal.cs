namespace TrProtocol.Packets;

public class SpiritHeal : Packet, IOtherPlayerSlot
{
    public override MessageID Type => MessageID.SpiritHeal;
    public byte OtherPlayerSlot { get; set; }
    public short Amount { get; set; }
}