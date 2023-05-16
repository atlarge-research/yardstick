namespace TrProtocol.Packets;

public class TeleportNPCThroughPortal : Packet, INPCSlot
{
    public override MessageID Type => MessageID.TeleportNPCThroughPortal;
    public short NPCSlot { get; set; }
    public ushort Extra { get; set; }
    public Vector2 Position { get; set; }
    public Vector2 Velocity { get; set; }
}