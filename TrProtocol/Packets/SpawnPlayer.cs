namespace TrProtocol.Packets;

public class SpawnPlayer : Packet, IPlayerSlot
{
    public override MessageID Type => MessageID.SpawnPlayer;
    public byte PlayerSlot { get; set; }
    public ShortPosition Position { get; set; }
    public int Timer { get; set; }
    public short DeathsPVE { get; set; }
    public short DeathsPVP { get; set; }
    public PlayerSpawnContext Context { get; set; }
}
