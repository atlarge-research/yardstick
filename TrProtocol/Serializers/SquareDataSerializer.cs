namespace TrProtocol.Models;

[Serializer(typeof(SquareDataSerializer))]
public partial class SquareData
{
    private class SquareDataSerializer : FieldSerializer<SquareData>
    {
        protected override SquareData ReadOverride(BinaryReader br)
        {
            var square = new SquareData()
            {
                TilePosX = br.ReadInt16(),
                TilePosY = br.ReadInt16(),
                Width = br.ReadByte(),
                Height = br.ReadByte(),
                ChangeType = (TileChangeType)br.ReadByte(),
            };
            square.Tiles = new SimpleTileData[square.Width, square.Height];
            for (int i = 0; i < square.Width; i++)
            {
                for (int j = 0; j < square.Height; j++)
                {
                    var tile = new SimpleTileData
                    {
                        Flags1 = br.ReadByte(),
                        Flags2 = br.ReadByte(),
                        Flags3 = br.ReadByte()
                    };
                    if (tile.Flags2[2])
                    {
                        tile.TileColor = br.ReadByte();
                    }
                    if (tile.Flags2[3])
                    {
                        tile.WallColor = br.ReadByte();
                    }
                    if (tile.Flags1[0])
                    {
                        tile.TileType = br.ReadUInt16();
                        if (Constants.tileFrameImportant[tile.TileType])
                        {
                            tile.FrameX = br.ReadInt16();
                            tile.FrameY = br.ReadInt16();
                        }
                    }
                    if (tile.Flags1[2])
                    {
                        tile.WallType = br.ReadUInt16();
                    }
                    if (tile.Flags1[3])
                    {
                        tile.Liquid = br.ReadByte();
                        tile.LiquidType = br.ReadByte();
                    }
                    square.Tiles[i, j] = tile;
                }
            }
            return square;
        }
        protected override void WriteOverride(BinaryWriter bw, SquareData t)
        {
            bw.Write(t.TilePosX);
            bw.Write(t.TilePosY);
            bw.Write(t.Width);
            bw.Write(t.Height);
            bw.Write((byte)t.ChangeType);
            for (int i = 0; i < t.Tiles.GetLength(0); i++)
            {
                for (int j = 0; j < t.Tiles.GetLength(1); j++)
                {
                    var tile = t.Tiles[i, j];
                    var flags1 = tile.Flags1;
                    var flags2 = tile.Flags2;
                    bw.Write(flags1);
                    bw.Write(flags2);

                    if (flags2[2])
                    {
                        bw.Write(tile.TileColor);
                    }
                    if (flags2[3])
                    {
                        bw.Write(tile.WallColor);
                    }
                    if (flags1[0])
                    {
                        bw.Write(tile.TileType);
                        if (Constants.tileFrameImportant[tile.TileType])
                        {
                            bw.Write(tile.FrameX);
                            bw.Write(tile.FrameY);
                        }
                    }
                    if (flags1[2])
                    {
                        bw.Write(tile.WallType);
                    }
                    if (flags1[3])
                    {
                        bw.Write(tile.Liquid);
                        bw.Write(tile.LiquidType);
                    }
                }
            }
        }
    }
}
