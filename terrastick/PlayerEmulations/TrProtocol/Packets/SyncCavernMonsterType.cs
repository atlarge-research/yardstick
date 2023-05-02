namespace TrProtocol.Packets;

public class SyncCavernMonsterType : Packet
{
    public override MessageID Type => MessageID.SyncCavernMonsterType;
    [ArraySize(6)]
    public short[] CavenMonsterType { get; set; }
}