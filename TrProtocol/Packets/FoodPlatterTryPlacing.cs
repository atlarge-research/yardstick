namespace TrProtocol.Packets;

public class FoodPlatterTryPlacing : Packet
{
    public override MessageID Type => MessageID.FoodPlatterTryPlacing;
    public ShortPosition Position { get; set; }
    public short ItemType { get; set; }
    public byte Prefix { get; set; }
    public short Stack { get; set; }
}