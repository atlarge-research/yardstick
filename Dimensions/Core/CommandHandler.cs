using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using TrProtocol.Packets.Modules;

namespace Dimensions.Core
{
    public class CommandHandler : ClientHandler
    {
        public override void OnC2SPacket(PacketReceiveArgs args)
        {
            if (args.Packet is not NetTextModuleC2S text) return;

            if (text.Text.StartsWith("/server"))
            {
                //var target = Program.config.GetServer(text.Text[7..].Trim());

                //Parent.ChangeServer(target);

                // handled raw player command
                args.Handled = true;
            }
        }
    }
}
