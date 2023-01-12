using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using TrProtocol;

namespace Dimensions.Core
{
    public class PacketReceiveArgs
    {
        public readonly Packet Packet;
        public bool Handled;

        public PacketReceiveArgs(Packet packet)
        {
            Packet = packet;
        }

    }
}
