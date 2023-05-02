namespace TrProtocol.Packets;

public class FishOutNPC : Packet
{
    public override MessageID Type => MessageID.FishOutNPC;
    public UShortPosition Position { get; set; }
    public short Start { get; set; }
}