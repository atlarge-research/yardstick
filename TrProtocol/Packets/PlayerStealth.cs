namespace TrProtocol.Packets;

public class PlayerStealth : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.PlayerStealth;
    public byte PlayerSlot { get; set; }
    public float Stealth { get; set; }
}