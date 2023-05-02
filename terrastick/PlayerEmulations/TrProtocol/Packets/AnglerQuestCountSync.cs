namespace TrProtocol.Packets;

public class AnglerQuestCountSync : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.AnglerQuestCountSync;
    public byte PlayerSlot { get; set; }
    public int AnglerQuestsFinished { get; set; }
    public int GolferScoreAccumulated { get; set; }
}