namespace TrProtocol.Packets;

public class Kick : Packet
{
    public override MessageID Type => MessageID.Kick;
    public NetworkText Reason { get; set; }
}
