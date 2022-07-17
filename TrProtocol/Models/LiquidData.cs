namespace TrProtocol.Models;

public partial struct LiquidData
{
    public ushort TotalChanges { get; set; }
    public LiquidChange[] LiquidChanges { get; set; }
}
