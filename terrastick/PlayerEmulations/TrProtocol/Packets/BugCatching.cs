namespace TrProtocol.Packets;

public class BugCatching : Packet, IPlayerSlot, INPCSlot
{
    public override MessageID Type => MessageID.BugCatching;
    public short NPCSlot { get; set; }
    public byte PlayerSlot { get; set; }
}