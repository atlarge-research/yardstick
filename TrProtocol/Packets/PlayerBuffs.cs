namespace TrProtocol.Packets
{
    public class PlayerBuffs : Packet, IPlayerSlot
    {
        public override MessageID Type => MessageID.PlayerBuffs;
        public byte PlayerSlot { get; set; }
        [ArraySize(22)]
        public ushort[] BuffTypes { get; set; }
    }
}