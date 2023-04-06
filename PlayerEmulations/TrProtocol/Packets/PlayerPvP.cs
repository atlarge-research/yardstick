namespace TrProtocol.Packets;

public class PlayerPvP : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.PlayerPvP;
    public byte PlayerSlot { get; set; }
    public bool Pvp { get; set; }
}