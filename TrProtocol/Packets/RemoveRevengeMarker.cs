namespace TrProtocol.Packets;

public class RemoveRevengeMarker : Packet
{
    public override MessageID Type => MessageID.RemoveRevengeMarker;
    public int ID { get; set; }
}