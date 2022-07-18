namespace TrProtocol.Packets;

public class ItemTweaker : Packet, IItemSlot
{
    public override MessageID Type => MessageID.ItemTweaker;
    public short ItemSlot { get; set; }
    public BitsByte Bit1 { get; set; }
    [Condition(nameof(Bit1), 0)] public uint PackedColor { get; set; }
    [Condition(nameof(Bit1), 1)] public ushort Damage { get; set; }
    [Condition(nameof(Bit1), 2)] public float Knockback { get; set; }
    [Condition(nameof(Bit1), 3)] public ushort UseAnimation { get; set; }
    [Condition(nameof(Bit1), 4)] public ushort UseTime { get; set; }
    [Condition(nameof(Bit1), 5)] public short Shoot { get; set; }
    [Condition(nameof(Bit1), 6)] public float ShootSpeed { get; set; }
    [Condition(nameof(Bit1), 7)] public BitsByte Bit2 { get; set; }
    [Condition(nameof(Bit2), 0)] public short Width { get; set; }
    [Condition(nameof(Bit2), 1)] public short Height { get; set; }
    [Condition(nameof(Bit2), 2)] public float Scale { get; set; }
    [Condition(nameof(Bit2), 3)] public short Ammo { get; set; }
    [Condition(nameof(Bit2), 4)] public short UseAmmo { get; set; }
    [Condition(nameof(Bit2), 4)] public bool NotAmmo { get; set; }
}