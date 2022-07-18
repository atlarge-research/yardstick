namespace TrProtocol.Packets;

public class NebulaLevelupRequest : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.NebulaLevelupRequest;
    public byte PlayerSlot { get; set; }
    public ushort NebulaType { get; set; }
    public Vector2 Position { get; set; }
}