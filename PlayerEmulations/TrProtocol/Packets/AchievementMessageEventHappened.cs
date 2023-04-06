namespace TrProtocol.Packets;

public class AchievementMessageEventHappened : Packet
{
    public override MessageID Type => MessageID.AchievementMessageEventHappened;
    public short EventType { get; set; }
}