using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using TrProtocol;
using TrProtocol.Models;

namespace Dimensions.Packets
{
    [Serializer(typeof(PrimitiveFieldSerializer<SubMessageID>))]
    public enum SubMessageID : short
    {
        ClientAddress = 1,
        ChangeSever = 2,
        ChangeCustomizedServer = 3,
        OnlineInfoRequest = 4,
        OnlineInfoResponse = 5
    }

    public class DimensionUpdate : Packet
    {
        public override MessageID Type => MessageID.Unused67;
        public SubMessageID SubType { get; set; }
        public string Content { get; set; }
        private bool ShouldHasPort => SubType == SubMessageID.ChangeCustomizedServer || SubType == SubMessageID.ClientAddress;
        [Condition(nameof(ShouldHasPort))]
        public ushort Port { get; set; }
    }
}
