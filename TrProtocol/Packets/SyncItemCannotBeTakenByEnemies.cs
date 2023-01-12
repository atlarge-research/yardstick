namespace TrProtocol.Packets;

public class SyncItemCannotBeTakenByEnemies : Packet, IItemBase
{
    public override MessageID Type => MessageID.SyncItemCannotBeTakenByEnemies;
    public short ItemSlot { get; set; }
    public Vector2 Position { get; set; }
    public Vector2 Velocity { get; set; }
    public short Stack { get; set; }
    public byte Prefix { get; set; }
    public byte Owner { get; set; }
    public short ItemType { get; set; }
    public bool Shimmered { get; set; }
    public byte TimeLeftInWhichTheItemCannotBeTakenByEnemies { get; set; }
}