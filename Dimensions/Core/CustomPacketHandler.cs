using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Dimensions.Models;
using Dimensions.Packets;
using TrProtocol.Models;
using TrProtocol.Packets.Modules;

namespace Dimensions.Core
{
    public class CustomPacketHandler : ClientHandler
    {
        public override void OnS2CPacket(PacketReceiveArgs args)
        {
            if (args.Packet is DimensionUpdate update)
            {
                Console.WriteLine($"dimension update received: {update}");
                switch (update.SubType)
                {
                    case SubMessageID.GetOnlineInfo:
                        Parent.SendChatMessage("Current Online: <not implemented>");
                        break;
                    case SubMessageID.ChangeSever:
                        var server = Program.config.GetServer(update.Content);

                        Parent.ChangeServer(server);
                        break;
                    case SubMessageID.ChangeCustomizedServer:
                        Parent.ChangeServer(new Server
                        {
                            name = "Customized Server",
                            serverIP = update.Content,
                            serverPort = update.Port
                        });
                        break;
                }
                args.Handled = true;
            }
        }
    }
}
