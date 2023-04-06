namespace TrProtocol.Packets;

public class SyncEquipment : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.SyncEquipment;
    public byte PlayerSlot { get; set; }
    public short ItemSlot { get; set; }
    public short Stack { get; set; }
    public byte Prefix { get; set; }
    public short ItemType { get; set; }
}
