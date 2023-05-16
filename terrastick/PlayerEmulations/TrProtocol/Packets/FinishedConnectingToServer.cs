namespace TrProtocol.Packets;

public class FinishedConnectingToServer : Packet
{
    public override MessageID Type => MessageID.FinishedConnectingToServer;
}