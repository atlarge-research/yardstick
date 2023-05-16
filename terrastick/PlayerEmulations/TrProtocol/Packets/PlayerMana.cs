namespace TrProtocol.Packets;

public class PlayerMana : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.PlayerMana;
    public byte PlayerSlot { get; set; }
    public short StatMana { get; set; }
    public short StatManaMax { get; set; }
}