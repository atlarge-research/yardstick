namespace TrProtocol.Packets;

public class PlayerActive : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.PlayerActive;
    public byte PlayerSlot { get; set; }
    public bool Active { get; set; }
}
