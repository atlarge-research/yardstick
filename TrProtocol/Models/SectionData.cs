namespace TrProtocol.Models;

public partial struct SectionData
{
    public int StartX { get; set; }
    public int StartY { get; set; }
    public short Width { get; set; }
    public short Height { get; set; }

    public ComplexTileData[] Tiles;
    public short ChestCount { get; set; }
    public ChestData[] Chests { get; set; }
    public short SignCount { get; set; }
    public SignData[] Signs { get; set; }
    public short TileEntityCount { get; set; }
    public TileEntity[] TileEntities { get; set; }
}
