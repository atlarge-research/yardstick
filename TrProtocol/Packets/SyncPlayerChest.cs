using TrProtocol.Models;

namespace TrProtocol.Packets;

public class SyncPlayerChest : Packet
{
    public override MessageID Type => MessageID.SyncPlayerChest;
    public short Chest { get; set; }
    public ShortPosition Position { get; set; }
    public byte[] Extra { get; set; }
}