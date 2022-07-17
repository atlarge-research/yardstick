namespace TrProtocol.Packets;

public class PlayNote : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.PlayNote;
    public byte PlayerSlot { get; set; }
    public float Range { get; set; }
}