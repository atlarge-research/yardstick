namespace TrProtocol.Packets;

public class PlayerHealth : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.PlayerHealth;
    public byte PlayerSlot { get; set; }
    public short StatLife { get; set; }
    public short StatLifeMax { get; set; }
}
