using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TrProtocol.Packets
{
    public class ClientHello : Packet
    {
        public override MessageID Type => MessageID.ClientHello;
        public string Version { get; set; }
    }
}
