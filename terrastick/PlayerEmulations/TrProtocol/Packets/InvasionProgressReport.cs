namespace TrProtocol.Packets;

public class InvasionProgressReport : Packet
{
    public override MessageID Type => MessageID.InvasionProgressReport;
    public int Progress { get; set; }
    public int ProgressMax { get; set; }
    public sbyte Icon { get; set; }
    public sbyte Wave { get; set; }
}