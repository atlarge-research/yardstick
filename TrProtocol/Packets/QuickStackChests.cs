namespace TrProtocol.Packets;

public class QuickStackChests : Packet
{
    public override MessageID Type => MessageID.QuickStackChests;
    public byte ChestSlot { get; set; }
}