using TrProtocol.Models;
using TrProtocol.Packets.Modules;

namespace Dimensions.Core;

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