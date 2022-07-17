namespace TrProtocol.Packets;

public class MassWireOperationPay : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.MassWireOperationPay;
    public short ItemType { get; set; }
    public short Stack { get; set; }
    public byte PlayerSlot { get; set; }
}