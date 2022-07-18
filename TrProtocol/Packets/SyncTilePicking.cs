namespace TrProtocol.Packets;

public class SyncTilePicking : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.SyncTilePicking;
    public byte PlayerSlot { get; set; }
    public ShortPosition Position { get; set; }
    public byte Damage { get; set; }
}