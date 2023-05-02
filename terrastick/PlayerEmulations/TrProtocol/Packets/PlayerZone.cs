namespace TrProtocol.Packets;

public class PlayerZone : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.PlayerZone;
    public byte PlayerSlot { get; set; }
    [ArraySize(5)]
    public byte[] Zone { get; set; }
}