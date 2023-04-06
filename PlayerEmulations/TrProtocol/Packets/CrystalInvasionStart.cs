namespace TrProtocol.Packets;

public class CrystalInvasionStart : Packet
{
    public override MessageID Type => MessageID.CrystalInvasionStart;
    public ShortPosition Position { get; set; }
}