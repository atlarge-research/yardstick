using TrProtocol.Packets;

namespace Dimensions.Core;

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