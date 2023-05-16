namespace TrProtocol.Packets;

public class SyncEmoteBubble : Packet
{
    public override MessageID Type => MessageID.SyncEmoteBubble;
    public int ID { get; set; }

    public byte EmoteType { get; set; }

    //FIXME: Terrible Format, can't understand
    public byte[] Raw { get; set; }
}