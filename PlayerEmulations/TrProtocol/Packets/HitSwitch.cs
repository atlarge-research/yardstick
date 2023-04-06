namespace TrProtocol.Packets;

public class HitSwitch : Packet
{
    public override MessageID Type => MessageID.HitSwitch;
    public ShortPosition Position { get; set; }
}