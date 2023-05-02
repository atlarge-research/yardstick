namespace TrProtocol.Packets;

public class CrystalInvasionSendWaitTime : Packet
{
    public override MessageID Type => MessageID.CrystalInvasionSendWaitTime;
    public int WaitTime { get; set; }
}