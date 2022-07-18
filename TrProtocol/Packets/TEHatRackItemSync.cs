namespace TrProtocol.Packets;

public class TEHatRackItemSync : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.TEHatRackItemSync;
    public byte PlayerSlot { get; set; }
    //FIXME: FUCKING TERRIBLE FORMAT
    public byte[] Extra { get; set; }
}