namespace TrProtocol.Packets;

public class SyncExtraValue : Packet
{
    public override MessageID Type => MessageID.SyncExtraValue;
    public short NPCSlot { get; set; }
    public int Extra { get; set; }
    public Vector2 MoneyPing { get; set; }
}