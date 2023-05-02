namespace TrProtocol.Packets;

public class TeleportPlayerThroughPortal : Packet, IOtherPlayerSlot
{
    public override MessageID Type => MessageID.TeleportPlayerThroughPortal;
    public byte OtherPlayerSlot { get; set; }
    public ushort Extra { get; set; }
    public Vector2 Position { get; set; }
    public Vector2 Velocity { get; set; }
}