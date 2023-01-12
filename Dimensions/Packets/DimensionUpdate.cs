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
    public enum SubMessageID
    {
        ChangeSever = 1,
        ChangeCustomizedServer = 2,
        GetOnlineInfo = 4
    }

    [S2COnly]
    public class DimensionUpdate : Packet
    {
        public override MessageID Type => MessageID.Unused67;
        public SubMessageID SubType { get; set; }
        public string Content { get; set; }
        private bool ShouldHasPort => SubType == SubMessageID.ChangeCustomizedServer;
        [Condition(nameof(ShouldHasPort))]
        public ushort Port { get; set; }
    }
}
