namespace TrProtocol.Packets;

public class SocialHandshake : Packet
{
    public override MessageID Type => MessageID.SocialHandshake;
    public byte[] Raw { get; set; }
}