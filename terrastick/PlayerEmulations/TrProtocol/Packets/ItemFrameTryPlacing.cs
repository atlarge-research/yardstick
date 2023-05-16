namespace TrProtocol.Packets;

public class ItemFrameTryPlacing : Packet
{
    public override MessageID Type => MessageID.ItemFrameTryPlacing;
    public ShortPosition Position { get; set; }
    public short ItemType { get; set; }
    public byte Prefix { get; set; }
    public short Stack { get; set; }
}