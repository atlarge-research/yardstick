using TrProtocol.Packets;

namespace Dimensions.Core;

public class NpcHandler : ClientHandler
{
    private const short maxNPC = 200;
    private readonly bool[] activeNpc = new bool[maxNPC];
    public override void OnCommonPacket(PacketReceiveArgs args)
    {
        if (args.Packet is SyncNPC npc)
            activeNpc[npc.NPCSlot] = npc.ShortHP > 0 || npc.PrettyShortHP > 0 || npc.HP > 0 || npc.Bit1[7] /* full hp */;
    }

    public override void OnCleaning()
    {
        for (short i = 0; i < maxNPC; ++i)
        {
            if (activeNpc[i])
            {
                Parent.SendClient(new SyncNPC
                {
                    NPCSlot = i,
                    Bit3 = 1,
                    Extra = Array.Empty<byte>()
                });
                activeNpc[i] = false;
            }
        }
    }
}