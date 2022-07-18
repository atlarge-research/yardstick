namespace TrProtocol.Packets;

public class ItemOwner : Packet, IItemSlot, IOtherPlayerSlot
{
    public override MessageID Type => MessageID.ItemOwner;
    public short ItemSlot { get; set; }
    public byte OtherPlayerSlot { get; set; }
}
