namespace TrProtocol.Packets;

public class PlayerTalkingNPC : Packet, IPlayerSlot, INPCSlot
{
    public override MessageID Type => MessageID.PlayerTalkingNPC;
    public byte PlayerSlot { get; set; }
    public short NPCSlot { get; set; }
}