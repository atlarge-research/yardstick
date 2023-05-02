namespace TrProtocol.Packets;

public class ResetItemOwner : Packet, IItemSlot
{
    public override MessageID Type => MessageID.ResetItemOwner;
    public short ItemSlot { get; set; }
}