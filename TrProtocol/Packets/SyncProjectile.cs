using TrProtocol.Models;

namespace TrProtocol.Packets
{
    public class SyncProjectile : Packet, IProjSlot, IPlayerSlot
    {
        public override MessageID Type => MessageID.SyncProjectile;
        public short ProjSlot { get; set; }
        public Vector2 Position { get; set; }
        public Vector2 Velocity { get; set; }
        public byte PlayerSlot { get; set; }
        [Bound("Terraria238", 955)]
        public short ProjType { get; set; }
        public BitsByte Bit1 { get; set; }
        [Condition("Bit1", 0)]
        public float AI1 { get; set; }
        [Condition("Bit1", 1)]
        public float AI2 { get; set; }
        [Condition("Bit1", 3)]
        public ushort BannerId { get; set; }
        [Condition("Bit1", 4)]
        public short Damange { get; set; }
        [Condition("Bit1", 5)]
        public float Knockback { get; set; }
        [Condition("Bit1", 6)]
        public ushort OriginalDamage { get; set; }
        [Condition("Bit1", 7)]
        public short UUID { get; set; }

    }
}