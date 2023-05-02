namespace TrProtocol.Packets;

public class RequestTileEntityInteraction : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.RequestTileEntityInteraction;
    public int TileEntityID { get; set; }
    public byte PlayerSlot { get; set; }
}