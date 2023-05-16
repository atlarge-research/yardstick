namespace TrProtocol.Packets;

public class SyncNPCName : Packet, INPCSlot
{
    public override MessageID Type => MessageID.SyncNPCName;
    public short NPCSlot { get; set; }
    [S2COnly]
    public string NPCName { get; set; }
    [S2COnly]
    public int TownNpc { get; set; }
}