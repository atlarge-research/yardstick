namespace TrProtocol.Packets;

public class RequestPassword : Packet
{
    public override MessageID Type => MessageID.RequestPassword;
}
