namespace TrProtocol.Packets;

public class UpdatePlayerLuckFactors : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.UpdatePlayerLuckFactors;
    public byte PlayerSlot { get; set; }
    public int Time { get; set; }
    public float Luck { get; set; }
    public byte Potion { get; set; }
    public bool HasGardenGnomeNearby { get; set; }
}