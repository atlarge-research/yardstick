namespace TrProtocol.Packets;

public class MoonlordCountdown : Packet
{
    public override MessageID Type => MessageID.MoonlordCountdown;
    public int MaxCountdown { get; set; }
    public int Countdown { get; set; }
}