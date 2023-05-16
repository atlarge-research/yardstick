namespace TrProtocol.Packets;

public class SendPassword : Packet
{
    public override MessageID Type => MessageID.SendPassword;
    public string Password { get; set; }
}
