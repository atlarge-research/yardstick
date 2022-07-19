namespace TrProtocol.Packets;

public class CombatTextInt : Packet
{
    public override MessageID Type => MessageID.CombatTextInt;
    public Vector2 Position { get; set; }
    public Color Color { get; set; }
    public int Amount { get; set; }
}