namespace TrProtocol.Models;

public struct LiquidChange
{
    public ShortPosition Position { get; set; }
    public byte LiquidAmount { get; set; }
    public LiquidType LiquidType { get; set; }
}
