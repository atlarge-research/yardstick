using TrProtocol.Serializers;

namespace TrProtocol.Models
{
    [Serializer(typeof(ByteEnumSerializer<TileChangeType>))]
    public enum TileChangeType : byte
    {
        None,
        LavaWater,
        HoneyWater,
        HoneyLava
    }
}
