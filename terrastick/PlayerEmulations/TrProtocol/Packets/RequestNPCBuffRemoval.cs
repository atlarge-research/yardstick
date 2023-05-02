namespace TrProtocol.Packets;

public class RequestNPCBuffRemoval : Packet, INPCSlot
{
    public override MessageID Type => MessageID.RequestNPCBuffRemoval;
    public short NPCSlot { get; set; }
    public ushort BuffType { get; set; }
}