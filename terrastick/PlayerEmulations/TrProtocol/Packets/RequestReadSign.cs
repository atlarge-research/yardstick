namespace TrProtocol.Packets;

public class RequestReadSign : Packet
{
    public override MessageID Type => MessageID.RequestReadSign;
    public ShortPosition Position { get; set; }
}