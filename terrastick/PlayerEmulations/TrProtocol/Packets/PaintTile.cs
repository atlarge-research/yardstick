namespace TrProtocol.Packets;

public class PaintTile : Packet
{
    public override MessageID Type => MessageID.PaintTile;
    public ShortPosition Position { get; set; }
    public byte Color { get; set; }
}