namespace TrProtocol.Packets;

public class ClientHello : Packet
{
    public override MessageID Type => MessageID.ClientHello;
    public string Version { get; set; }
}
