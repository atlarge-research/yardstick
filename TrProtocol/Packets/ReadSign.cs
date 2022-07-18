namespace TrProtocol.Packets;

public class ReadSign : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.ReadSign;
    public short SignSlot { get; set; }
    public ShortPosition Position { get; set; }
    public string Text { get; set; }
    public byte PlayerSlot { get; set; }
    public byte Bit1 { get; set; }
}