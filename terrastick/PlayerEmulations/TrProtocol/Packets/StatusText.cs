namespace TrProtocol.Packets;

public class StatusText : Packet
{
    public override MessageID Type => MessageID.StatusText;
    public int Max { get; set; }
    public NetworkText Text { get; set; }
    public byte Flag { get; set; }
}
