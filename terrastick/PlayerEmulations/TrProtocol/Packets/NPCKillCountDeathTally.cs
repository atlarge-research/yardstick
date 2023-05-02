namespace TrProtocol.Packets;

public class NPCKillCountDeathTally : Packet
{
    public override MessageID Type => MessageID.NPCKillCountDeathTally;
    public short NPCType { get; set; }
    public int Count { get; set; }
}