namespace TrProtocol.Packets;

public class SendNPCBuffs : Packet, INPCSlot
{
    public override MessageID Type => MessageID.SendNPCBuffs;
    public short NPCSlot { get; set; }
    [ArraySize(20)]
    public Buff[] Buffs { get; set; }
}