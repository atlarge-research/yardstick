namespace TrProtocol.Packets;

public class SyncLoadout : Packet, IPlayerSlot, ILoadOutSlot
{
    public override MessageID Type => MessageID.SyncLoadout;
    public byte PlayerSlot { get; set; }
    public byte LoadOutSlot { get; set; }
    public ushort AccessoryVisibility { get; set; }
}