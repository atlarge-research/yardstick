namespace TrProtocol.Packets;

public class BugReleasing : Packet
{
    public override MessageID Type => MessageID.BugReleasing;
    public Position Position { get; set; }
    public short NPCType { get; set; }
    public byte Style { get; set; }
}