namespace TrProtocol.Packets;

public class GemLockToggle : Packet
{
    public override MessageID Type => MessageID.GemLockToggle;
    public ShortPosition Position { get; set; }
    public bool Flag { get; set; }
}