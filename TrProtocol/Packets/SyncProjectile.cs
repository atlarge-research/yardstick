namespace TrProtocol.Packets;

public class SyncProjectile : Packet, IProjSlot, IPlayerSlot
{
    public override MessageID Type => MessageID.SyncProjectile;
    public short ProjSlot { get; set; }
    public Vector2 Position { get; set; }
    public Vector2 Velocity { get; set; }
    public byte PlayerSlot { get; set; }
    [Bounds("Terraria238", 955)]
    public short ProjType { get; set; }
    public BitsByte Bit1 { get; set; }
    [Condition(nameof(Bit1), 0)]
    public float AI1 { get; set; }
    [Condition(nameof(Bit1), 1)]
    public float AI2 { get; set; }
    [Condition(nameof(Bit1), 3)]
    public ushort BannerId { get; set; }
    [Condition(nameof(Bit1), 4)]
    public short Damange { get; set; }
    [Condition(nameof(Bit1), 5)]
    public float Knockback { get; set; }
    [Condition(nameof(Bit1), 6)]
    public ushort OriginalDamage { get; set; }
    [Condition(nameof(Bit1), 7)]
    public short UUID { get; set; }

}