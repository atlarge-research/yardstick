namespace TrProtocol.Packets;

public class SyncPlayerChest : Packet
{
    public override MessageID Type => MessageID.SyncPlayerChest;
    public short Chest { get; set; }
    public ShortPosition Position { get; set; }
    public byte NameLength { get; set; }
    private bool _shouldSerializeName
        => NameLength is > 0 and <= 20;
    [Condition(nameof(_shouldSerializeName))]
    public string Name { get; set; }
}