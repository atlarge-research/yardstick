namespace TrProtocol.Packets;

public class FrameSection : Packet
{
    public override MessageID Type => MessageID.FrameSection;
    public ShortPosition Start { get; set; }
    public ShortPosition End { get; set; }
}
