namespace TrProtocol.Packets;

public class ChestName : Packet
{
    public override MessageID Type => MessageID.ChestName;
    public short ChestSlot { get; set; }
    public ShortPosition Position { get; set; }
    public string Name { get; set; }
}