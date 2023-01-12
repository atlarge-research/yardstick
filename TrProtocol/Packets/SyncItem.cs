namespace TrProtocol.Packets;

public class SyncItem : Packet, IItemBase
{
    public override MessageID Type => MessageID.SyncItem;
    public short ItemSlot { get; set; }
    public Vector2 Position { get; set; }
    public Vector2 Velocity { get; set; }
    public short Stack { get; set; }
    public byte Prefix { get; set; }
    public byte Owner { get; set; }
    public short ItemType { get; set; }
}
