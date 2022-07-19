namespace TrProtocol.Packets;

public class TileSection : Packet
{
    public override MessageID Type => MessageID.TileSection;
    public SectionData Data { get; set; }
}
