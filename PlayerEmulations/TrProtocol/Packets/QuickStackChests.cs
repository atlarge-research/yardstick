namespace TrProtocol.Packets;

public class QuickStackChests : Packet, IChestSlot
{
    public override MessageID Type => MessageID.QuickStackChests;
    public short ChestSlot { get; set; }
}