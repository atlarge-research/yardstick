using TrProtocol;
using TrProtocol.Models;
using TrProtocol.Packets;
using TrProtocol.Packets.Modules;

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


public class PlayerHandler : ClientHandler
{
    private const byte maxPlayer = 254;
    private readonly bool[] activePlayers = new bool[maxPlayer];
    public override void OnCommonPacket(PacketReceiveArgs args)
    {
        if (args.Packet is PlayerActive act)
            activePlayers[act.PlayerSlot] = act.Active;
    }

    public override void OnCleaning()
    {
        for (byte i = 0; i < maxPlayer; ++i)
        {
            if (activePlayers[i])
            {
                Parent.SendClient(new PlayerActive
                {
                    PlayerSlot = i,
                    Active = false
                });
                activePlayers[i] = false;
            }
        }
    }
}

public class ProjectileHandler : ClientHandler
{
    private const short maxProjectile = 1000;
    private readonly short[] projOwner = new short[maxProjectile];

    public ProjectileHandler()
    {
        for (short i = 0; i < maxProjectile; ++i) projOwner[i] = -1;
    }
    public override void OnCommonPacket(PacketReceiveArgs args)
    {
        if (args.Packet is SyncProjectile sync)
            projOwner[sync.ProjSlot] = sync.PlayerSlot;
        else if (args.Packet is KillProjectile kill)
            if (projOwner[kill.ProjSlot] == kill.PlayerSlot)
                projOwner[kill.PlayerSlot] = -1;
    }

    public override void OnCleaning()
    {
        for (short i = 0; i < maxProjectile; ++i)
        {
            if (projOwner[i] != -1)
            {
                Parent.SendClient(new KillProjectile
                {
                    PlayerSlot = (byte)projOwner[i],
                    ProjSlot = i
                });
                projOwner[i] = -1;
            }
        }
    }
}

public class PylonHandler : ClientHandler
{
    private const byte maxPylon = 9;
    private readonly ShortPosition[] activePylon = new ShortPosition[maxPylon];

    public PylonHandler()
    {
        for (short i = 0; i < maxPylon; ++i) 
            activePylon[i] = new ShortPosition(-1, -1);
    }

    public override void OnCommonPacket(PacketReceiveArgs args)
    {
        if (args.Packet is NetTeleportPylonModule pylon)
            if (pylon.PylonPacketType == PylonPacketType.PylonWasAdded)
                activePylon[(int) pylon.PylonType] = pylon.Position;
            else
                activePylon[(int)pylon.PylonType] = new ShortPosition(-1, -1);
    }

    public override void OnCleaning()
    {
        for (short i = 0; i < maxPylon; ++i)
        {
            if (activePylon[i].X >= 0 && activePylon[i].Y >= 0)
            {
                Parent.SendClient(new NetTeleportPylonModule
                {
                    PylonPacketType = PylonPacketType.PylonWasRemoved,
                    PylonType = (TeleportPylonType) i,
                    Position = activePylon[i]
                });
                activePylon[i] = new ShortPosition(-1, -1);
            }
        }
    }
}


public class ItemHandler : ClientHandler
{
    private const short maxItem = 401;
    private readonly bool[] activeItem = new bool[maxItem];
    public override void OnCommonPacket(PacketReceiveArgs args)
    {
        if (args.Packet is IItemBase sync)
            activeItem[sync.ItemSlot] = sync.ItemType != 0;
    }

    public override void OnCleaning()
    {
        for (short i = 0; i < maxItem; ++i)
        {
            if (activeItem[i])
            {
                Parent.SendClient(new SyncItem()
                {
                    ItemSlot = i,
                    ItemType = 0
                });
                activeItem[i] = false;
            }
        }
    }
}
