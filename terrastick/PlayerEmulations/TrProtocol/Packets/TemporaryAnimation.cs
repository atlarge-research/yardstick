namespace TrProtocol.Packets;

public class TemporaryAnimation : Packet
{
    public override MessageID Type => MessageID.TemporaryAnimation;
    public short AniType { get; set; }
    public short TileType { get; set; }
    public ShortPosition Position { get; set; }
}