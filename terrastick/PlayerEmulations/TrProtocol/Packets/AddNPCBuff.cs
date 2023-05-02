namespace TrProtocol.Packets;

public class AddNPCBuff : Packet, INPCSlot
{
    public override MessageID Type => MessageID.AddNPCBuff;
    public short NPCSlot { get; set; }
    public ushort BuffType { get; set; }
    public short BuffTime { get; set; }
}