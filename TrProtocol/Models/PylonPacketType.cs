using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using TrProtocol.Serializers;

namespace TrProtocol.Models
{
    [Serializer(typeof(ByteEnumSerializer<PylonPacketType>))]
    public enum PylonPacketType : byte
    {
        PylonWasAdded,
        PylonWasRemoved,
        PlayerRequestsTeleport
    }
}
