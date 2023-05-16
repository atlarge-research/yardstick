namespace TrProtocol.Packets;

public class PlayerTeam : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.PlayerTeam;
    public byte PlayerSlot { get; set; }
    public byte Team { get; set; }
}