namespace TrProtocol.Packets;

public class AchievementMessageNPCKilled : Packet
{
    public override MessageID Type => MessageID.AchievementMessageNPCKilled;
    public short NPCType { get; set; }
}