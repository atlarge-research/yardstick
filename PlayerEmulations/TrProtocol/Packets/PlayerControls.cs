namespace TrProtocol.Packets;

public class PlayerControls : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.PlayerControls;
    public byte PlayerSlot { get; set; }
    public BitsByte Bit1 { get; set; }
    public BitsByte Bit2 { get; set; }
    public BitsByte Bit3 { get; set; }
    public BitsByte Bit4 { get; set; }
    public byte SelectedItem { get; set; }
    public Vector2 Position { get; set; }
    [Condition(nameof(Bit2), 2)]
    public Vector2 Velocity { get; set; }
    [Condition(nameof(Bit3), 6)]
    public Vector2 PotionOfReturnOriginalUsePosition { get; set; }
    [Condition(nameof(Bit3), 6)]
    public Vector2 PotionOfReturnHomePosition { get; set; }
}
