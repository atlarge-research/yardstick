namespace TrProtocol.Packets;

public class RequestChestOpen : Packet
{
    public override MessageID Type => MessageID.RequestChestOpen;
    public ShortPosition Position { get; set; }
}