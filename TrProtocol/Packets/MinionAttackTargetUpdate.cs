namespace TrProtocol.Packets;

public class MinionAttackTargetUpdate : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.MinionAttackTargetUpdate;
    public byte PlayerSlot { get; set; }
    public short MinionAttackTarget { get; set; }
}