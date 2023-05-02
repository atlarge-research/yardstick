namespace TrProtocol.Packets;

public class PlayerDeathV2 : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.PlayerDeathV2;
    public byte PlayerSlot { get; set; }
    public PlayerDeathReason Reason { get; set; }
    public short Damage { get; set; }
    public byte HitDirection { get; set; }
    public BitsByte Bits1 { get; set; }
}