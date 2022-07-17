namespace TrProtocol.Packets;

public class SetCountsAsHostForGameplay : Packet, IOtherPlayerSlot
{
    public override MessageID Type => MessageID.SetCountsAsHostForGameplay;
    public byte OtherPlayerSlot { get; set; }
    public bool Flag { get; set; }
}