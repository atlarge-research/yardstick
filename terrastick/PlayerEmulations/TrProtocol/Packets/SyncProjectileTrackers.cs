namespace TrProtocol.Packets;

public class SyncProjectileTrackers : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.SyncProjectileTrackers;
    public byte PlayerSlot { get; set; }
    public short ExpectedOwner1 { get; set; }
    private bool HasOwner1 => ExpectedOwner1 != -1;

    [Condition(nameof(HasOwner1))]
    public short ExpectedIdentity1 { get; set; }
    [Condition(nameof(HasOwner1))]
    public short ExpectedType1 { get; set; }
    public short ExpectedOwner2 { get; set; }
    private bool HasOwner2 => ExpectedOwner2 != -1;

    [Condition(nameof(HasOwner2))]
    public short ExpectedIdentity2 { get; set; }
    [Condition(nameof(HasOwner2))]
    public short ExpectedType2 { get; set; }
}