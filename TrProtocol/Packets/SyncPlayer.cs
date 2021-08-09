using TrProtocol.Models;

namespace TrProtocol.Packets
{
    public class SyncPlayer : Packet, IPlayerSlot
    {
        public override MessageID Type => MessageID.SyncPlayer;
        public byte PlayerSlot { get; set; }
        public byte SkinVariant { get; set; }
        public byte Hair { get; set; }
        public string Name { get; set; }
        public byte HairDye { get; set; }
        public byte HideMisc { get; set; }
        public Color HairColor { get; set; }
        public Color SkinColor { get; set; }
        public Color EyeColor { get; set; }
        public Color ShirtColor { get; set; }
        public Color UnderShirtColor { get; set; }
        public Color PantsColor { get; set; }
        public Color ShoeColor { get; set; }
        public BitsByte Bit { get; set; }
    }
}
