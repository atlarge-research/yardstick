namespace TrProtocol.Packets;

public class MurderSomeoneElsesProjectile : Packet, IOtherPlayerSlot
{
    public override MessageID Type => MessageID.MurderSomeoneElsesProjectile;
    public byte OtherPlayerSlot { get; set; }
    public byte HighBitOfPlayerIsAlwaysZero { get; set; } = 0;
    public byte AI1 { get; set; }
}