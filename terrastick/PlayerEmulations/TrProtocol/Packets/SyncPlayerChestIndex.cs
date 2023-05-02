namespace TrProtocol.Packets;

public class SyncPlayerChestIndex : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.SyncPlayerChestIndex;
    public byte PlayerSlot { get; set; }
    public short ChestIndex { get; set; }
}