namespace TrProtocol.Packets;

public class ChestUpdates : Packet
{
    public override MessageID Type => MessageID.ChestUpdates;
    public byte Operation { get; set; }
    public ShortPosition Position { get; set; }
    public short Style { get; set; }
    public short ChestSlot { get; set; }
}