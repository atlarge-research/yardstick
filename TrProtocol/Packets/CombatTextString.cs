namespace TrProtocol.Packets;

public class CombatTextString : Packet
{
    public override MessageID Type => MessageID.CombatTextString;
    public Vector2 Position { get; set; }
    public Color Color { get; set; }
    public NetworkText Text { get; set; }
}