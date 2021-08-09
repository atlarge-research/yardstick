namespace TrProtocol.Packets
{
    public class ItemOwner : Packet, IItemSlot, IPlayerSlot
    {
        public override MessageID Type => MessageID.ItemOwner;
        public byte ItemSlot { get; set; }
        public byte PlayerSlot { get; set; }
    }
}
