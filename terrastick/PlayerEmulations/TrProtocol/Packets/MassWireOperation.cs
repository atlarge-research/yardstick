namespace TrProtocol.Packets;

public class MassWireOperation : Packet
{
    public override MessageID Type => MessageID.MassWireOperation;
    public ShortPosition Start { get; set; }
    public ShortPosition End { get; set; }
    public MultiToolMode Mode { get; set; }
}