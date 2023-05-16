namespace TrProtocol.Packets;

public class TileCounts : Packet
{
    public override MessageID Type => MessageID.TileCounts;
    public byte Good { get; set; }
    public byte Evil { get; set; }
    public byte Blood { get; set; }
}