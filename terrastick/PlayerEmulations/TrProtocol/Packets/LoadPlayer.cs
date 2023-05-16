namespace TrProtocol.Packets;

public class LoadPlayer : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.LoadPlayer;
    public byte PlayerSlot { get; set; }
    public bool ServerWantsToRunCheckBytesInClientLoopThread { get; set; }
}
