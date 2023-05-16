namespace TrProtocol.Packets;

public class SpawnBoss : Packet, IOtherPlayerSlot
{
    public override MessageID Type => MessageID.SpawnBoss;
    public byte OtherPlayerSlot { get; set; }
    public byte HighBitOfPlayerIsAlwaysZero { get; set; } = 0;
    public short NPCType { get; set; }
}