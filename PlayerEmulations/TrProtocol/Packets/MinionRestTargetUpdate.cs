namespace TrProtocol.Packets;

public class MinionRestTargetUpdate : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.MinionRestTargetUpdate;
    public byte PlayerSlot { get; set; }
    public Vector2 MinionRestTargetPoint { get; set; }
}