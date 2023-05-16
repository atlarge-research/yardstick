namespace TrProtocol.Packets;

public class SmartTextMessage : Packet
{
    public override MessageID Type => MessageID.SmartTextMessage;
    public Color Color { get; set; }
    public NetworkText Text { get; set; }
    public short Width { get; set; }
}
