namespace TrProtocol.Packets;

public class AnglerQuest : Packet
{
    public override MessageID Type => MessageID.AnglerQuest;
    public byte QuestType { get; set; }
    public bool Finished { get; set; }
}