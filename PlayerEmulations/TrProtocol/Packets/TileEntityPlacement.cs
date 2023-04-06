namespace TrProtocol.Packets;

public class TileEntityPlacement : Packet
{
    public override MessageID Type => MessageID.TileEntityPlacement;
    public ShortPosition Position { get; set; }
    public byte TileEntityType { get; set; }
}