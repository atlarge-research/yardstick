namespace TrProtocol.Models;

[Serializer(typeof(PrimitiveFieldSerializer<LiquidType>))]
public enum LiquidType : byte
{
    Water = 1,
    Lava = 2,
    Honey = 3
}
