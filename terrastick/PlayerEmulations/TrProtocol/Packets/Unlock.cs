namespace TrProtocol.Packets;

public class Unlock : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.Unlock;
    public byte PlayerSlot { get; set; }
    public ShortPosition Position { get; set; }
}