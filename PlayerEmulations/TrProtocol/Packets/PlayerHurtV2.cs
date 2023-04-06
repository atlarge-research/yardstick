namespace TrProtocol.Packets;

public class PlayerHurtV2 : Packet, IOtherPlayerSlot
{
    public override MessageID Type => MessageID.PlayerHurtV2;
    public byte OtherPlayerSlot { get; set; }
    public PlayerDeathReason Reason { get; set; }
    public short Damage { get; set; }
    public byte HitDirection { get; set; }
    public BitsByte Bits1 { get; set; }
    public sbyte CoolDown { get; set; }
}