namespace TrProtocol.Models;

public struct SimpleTileData
{
    public BitsByte Flags1;
    public BitsByte Flags2;
    public BitsByte Flags3;
    public byte TileColor { get; set; }
    public byte WallColor { get; set; }
    public ushort TileType { get; set; }
    public short FrameX { get; set; }
    public short FrameY { get; set; }
    public ushort WallType { get; set; }
    public byte Liquid { get; set; }
    public byte LiquidType { get; set; }
}
