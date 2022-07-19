namespace TrProtocol.Packets;

public class LandGolfBallInCup : Packet, IOtherPlayerSlot
{
    public override MessageID Type => MessageID.LandGolfBallInCup;
    public byte OtherPlayerSlot { get; set; }
    public UShortPosition Position { get; set; }
    public ushort Hits { get; set; }
    public ushort ProjType { get; set; }
}