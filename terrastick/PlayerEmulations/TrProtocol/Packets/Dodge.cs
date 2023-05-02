namespace TrProtocol.Packets;

public class Dodge : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.Dodge;
    public byte PlayerSlot { get; set; }
    public byte DodgeType { get; set; }
}