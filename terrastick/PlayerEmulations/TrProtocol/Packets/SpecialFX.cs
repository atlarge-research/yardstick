namespace TrProtocol.Packets;

public class SpecialFX : Packet
{
    public override MessageID Type => MessageID.SpecialFX;
    public byte GrowType { get; set; }
    public Position Position { get; set; }
    public byte Height { get; set; }
    public short Gore { get; set; }
}