using TrProtocol.Serializers;

namespace TrProtocol.Models
{
    [Serializer(typeof(ByteEnumSerializer<LogicCheckType>))]
    public enum LogicCheckType : byte
    {
        None,
        Day,
        Night,
        PlayerAbove,
        Water,
        Lava,
        Honey,
        Liquid
    }
}
