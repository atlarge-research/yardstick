namespace TrProtocol.Packets;

public class TEHatRackItemSync : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.TEHatRackItemSync;
    public byte PlayerSlot { get; set; }
    public int TileEntityID { get; set; }
    public byte ItemSlot { get; set; }
    public ushort ItemID { get; set; }
    public ushort Stack { get; set; }
    public byte Prefix { get; set; }
}