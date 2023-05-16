namespace TrProtocol.Packets;

public class ClientUUID : Packet
{
    public override MessageID Type => MessageID.ClientUUID;
    public string UUID { get; set; }
}