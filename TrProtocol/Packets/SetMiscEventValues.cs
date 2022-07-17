namespace TrProtocol.Packets;

public class SetMiscEventValues : Packet, IOtherPlayerSlot
{
    public override MessageID Type => MessageID.SetMiscEventValues;
    public byte OtherPlayerSlot { get; set; }
    public int CreditsRollTime { get; set; }
}