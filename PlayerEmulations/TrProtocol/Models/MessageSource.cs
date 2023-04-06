using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TrProtocol.Models;

[Serializer(typeof(PrimitiveFieldSerializer<MessageSource>))]
public enum MessageSource : byte
{
    Idle,
    Storage,
    ThrownAway,
    PickedUp,
    ChoppedTree,
    ChoppedGemTree,
    ChoppedCactus,
    Count
}