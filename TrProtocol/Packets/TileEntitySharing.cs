namespace TrProtocol.Packets;

public class TileEntitySharing : Packet
{
    public override MessageID Type => MessageID.TileEntitySharing;
    public int ID { get; set; }
    public bool IsNew { get; set; }
    [Condition(nameof(IsNew))] public TileEntity Entity { get; set; }
}