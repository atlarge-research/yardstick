namespace TrProtocol.Packets;

public class SyncChestItem : Packet
{
    public override MessageID Type => MessageID.SyncChestItem;
    public short ChestSlot { get; set; }
    public byte ChestItemSlot { get; set; }
    public short Stack { get; set; }
    public byte Prefix { get; set; }
    public short ItemType { get; set; }
}