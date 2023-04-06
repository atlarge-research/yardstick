namespace TrProtocol.Packets;

public class TileSquare : Packet
{
    public override MessageID Type => MessageID.TileSquare;
    public SquareData Data { get; set; }
}
