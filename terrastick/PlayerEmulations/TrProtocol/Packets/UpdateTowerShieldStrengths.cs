namespace TrProtocol.Packets;

public class UpdateTowerShieldStrengths : Packet
{
    public override MessageID Type => MessageID.UpdateTowerShieldStrengths;
    [ArraySize(4)] public ushort[] ShieldStrength { get; set; }
}