namespace TrProtocol.Packets;

public class StartPlaying : Packet
{
    public override MessageID Type => MessageID.StartPlaying;
}
