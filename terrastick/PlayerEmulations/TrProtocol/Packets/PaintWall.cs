namespace TrProtocol.Packets;

public class PaintWall : Packet
{
    public override MessageID Type => MessageID.PaintWall;
    public ShortPosition Position { get; set; }
    public byte Color { get; set; }
}