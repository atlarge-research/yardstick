namespace TrProtocol.Packets;

public class HealEffect : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.HealEffect;
    public byte PlayerSlot { get; set; }
    public short Amount { get; set; }
}