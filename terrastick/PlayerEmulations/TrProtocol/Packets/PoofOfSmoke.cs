namespace TrProtocol.Packets;

public class PoofOfSmoke : Packet
{
    public override MessageID Type => MessageID.PoofOfSmoke;
    public uint PackedHalfVector2 { get; set; }
}