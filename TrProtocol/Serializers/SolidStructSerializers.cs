namespace TrProtocol.Models;

[Serializer(typeof(BitsByteSerializer))]
public partial struct BitsByte
{
    private class BitsByteSerializer : PrimitiveFieldSerializer<BitsByte>
    {
    }
}

[Serializer(typeof(Vector2Serailizer))]
public partial struct Vector2
{
    public class Vector2Serailizer : PrimitiveFieldSerializer<Vector2>
    {
    }
}

[Serializer(typeof(PositionSerailizer))]
public partial struct Position
{
    public class PositionSerailizer : PrimitiveFieldSerializer<Position>
    {
    }
}

[Serializer(typeof(ShortPositionSerializer))]
public partial struct ShortPosition
{
    private class ShortPositionSerializer : PrimitiveFieldSerializer<ShortPosition>
    {
    }
}

[Serializer(typeof(UShortPositionSerializer))]
public partial struct UShortPosition
{
    private class UShortPositionSerializer : PrimitiveFieldSerializer<UShortPosition>
    {
    }
}

