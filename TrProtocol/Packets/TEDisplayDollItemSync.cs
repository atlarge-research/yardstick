namespace TrProtocol.Packets;

public class TEDisplayDollItemSync : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.TEDisplayDollItemSync;
    public byte PlayerSlot { get; set; }
    //FIXME: FUCKING TERRIBLE FORMAT
    public byte[] Extra { get; set; }
}