namespace TrProtocol.Packets;
public class TogglePvp : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.TogglePvp;
    public byte PlayerSlot { get; set; }
    public bool PvpEnabled { get; set; }
}