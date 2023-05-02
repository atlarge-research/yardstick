namespace TrProtocol.Packets;

public class ItemAnimation : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.ItemAnimation;
    public byte PlayerSlot { get; set; }
    public float Rotation { get; set; }
    public short Animation { get; set; }
}