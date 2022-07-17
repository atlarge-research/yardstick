namespace TrProtocol.Packets;

public class Emoji : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.Emoji;
    public byte PlayerSlot { get; set; }
    public byte Emote { get; set; }
}