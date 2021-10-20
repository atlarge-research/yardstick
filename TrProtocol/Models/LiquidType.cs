using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using TrProtocol.Serializers;

namespace TrProtocol.Models
{
    [Serializer(typeof(ByteEnumSerializer<LiquidType>))]
    public enum LiquidType : byte
    {
        Water = 1,
        Lava = 2,
        Honey = 3
    }
}
