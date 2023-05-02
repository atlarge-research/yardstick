namespace TrProtocol.Packets;

public class Assorted1 : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.Assorted1;
    public byte PlayerSlot { get; set; }
    public byte Unknown { get; set; }
}