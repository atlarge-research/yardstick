using TrProtocol.Packets.Mobile;

namespace Dimensions.Core;

public class MobileHandler : ClientHandler
{
    public override void OnC2SPacket(PacketReceiveArgs args)
    {
        if (args.Packet is PlayerPlatformInfo packet)
        {
            Parent.SendChatMessage($"[DEBUG]: PE Client Detected(platform={packet.PlatformId}, playerid={packet.PlayerId})");
        }
    }
}