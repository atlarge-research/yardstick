namespace TrProtocol.Packets;

public class KillProjectile : Packet, IProjSlot, IPlayerSlot
{
    public override MessageID Type => MessageID.KillProjectile;
    public short ProjSlot { get; set; }
    public byte PlayerSlot { get; set; }
}