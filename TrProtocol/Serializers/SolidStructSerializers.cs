namespace TrProtocol.Models;


[Serializer(typeof(PrimitiveFieldSerializer<BitsByte>))]
public partial struct BitsByte
{
}

[Serializer(typeof(PrimitiveFieldSerializer<Vector2>))]
public partial struct Vector2
{
}

[Serializer(typeof(PrimitiveFieldSerializer<ShortPosition>))]
public partial struct ShortPosition
{
}

[Serializer(typeof(PrimitiveFieldSerializer<Buff>))]
public partial struct Buff
{
}

[Serializer(typeof(PrimitiveFieldSerializer<UShortPosition>))]
public partial struct UShortPosition
{
}

[Serializer(typeof(PrimitiveFieldSerializer<Position>))]
public partial struct Position
{
}