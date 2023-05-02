namespace TrProtocol.Packets;

public class WeaponsRackTryPlacing : Packet
{
    public override MessageID Type => MessageID.WeaponsRackTryPlacing;
    public ShortPosition Position { get; set; }
    public short ItemType { get; set; }
    public byte Prefix { get; set; }
    public short Stack { get; set; }
}