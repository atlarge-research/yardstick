namespace TrProtocol.Packets;

public class DeadPlayer : Packet, IOtherPlayerSlot
{
    public override MessageID Type => MessageID.DeadPlayer;
    public byte OtherPlayerSlot { get; set; }
}