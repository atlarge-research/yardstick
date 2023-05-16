namespace TrProtocol.Packets;

public class SyncItemsWithShimmer : Packet, IItemBase
{
    public override MessageID Type => MessageID.SyncItemsWithShimmer;
    public short ItemSlot { get; set; }
    public Vector2 Position { get; set; }
    public Vector2 Velocity { get; set; }
    public short Stack { get; set; }
    public byte Prefix { get; set; }
    public byte Owner { get; set; }
    public short ItemType { get; set; }
    public bool Shimmered { get; set; }
    public float ShimmerTime { get; set; }
}