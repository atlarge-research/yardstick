namespace TrProtocol.Models;

public partial class SquareData
{
    public short TilePosX { get; set; }
    public short TilePosY { get; set; }
    public byte Width { get; set; }
    public byte Height { get; set; }
    public TileChangeType ChangeType { get; set; }
    public SimpleTileData[,] Tiles { get; set; }
}
