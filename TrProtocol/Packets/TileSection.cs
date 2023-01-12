namespace TrProtocol.Packets;

public class TileSection : Packet
{
    public override MessageID Type => MessageID.TileSection;
    //public byte[] data { get; set; }
    public SectionData Data { get; set; }
}
