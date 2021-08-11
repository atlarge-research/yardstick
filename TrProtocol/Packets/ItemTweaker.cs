using TrProtocol.Models;

namespace TrProtocol.Packets
{
    public class ItemTweaker : Packet, IItemSlot
    {
        public override MessageID Type => MessageID.ItemTweaker;
        public short ItemSlot { get; set; }
        public BitsByte Bit1 { get; set; }
        [Condition("Bit1", 0)] public uint PackedColor { get; set; }
        [Condition("Bit1", 1)] public ushort Damage { get; set; }
        [Condition("Bit1", 2)] public float Knockback { get; set; }
        [Condition("Bit1", 3)] public ushort UseAnimation { get; set; }
        [Condition("Bit1", 4)] public ushort UseTime { get; set; }
        [Condition("Bit1", 5)] public short Shoot { get; set; }
        [Condition("Bit1", 6)] public float ShootSpeed { get; set; }
        [Condition("Bit1", 7)] public BitsByte Bit2 { get; set; }
        [Condition("Bit2", 0)] public short Width { get; set; }
        [Condition("Bit2", 1)] public short Height { get; set; }
        [Condition("Bit2", 2)] public float Scale { get; set; }
        [Condition("Bit2", 3)] public short Ammo { get; set; }
        [Condition("Bit2", 4)] public short UseAmmo { get; set; }
        [Condition("Bit2", 4)] public bool NotAmmo { get; set; }
    }
}