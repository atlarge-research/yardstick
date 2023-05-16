namespace TrProtocol.Packets;

public class TeleportationPotion : Packet
{
    public override MessageID Type => MessageID.TeleportationPotion;
    public byte Style { get; set; }
}