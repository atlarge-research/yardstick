namespace TrProtocol.Packets;

public class ManaEffect : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.ManaEffect;
    public byte PlayerSlot { get; set; }
    public short Amount { get; set; }
}