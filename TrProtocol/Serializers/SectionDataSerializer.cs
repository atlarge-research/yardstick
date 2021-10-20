using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;

namespace TrProtocol.Models
{
    [Serializer(typeof(SectionDataSerializer))]
    public partial struct SectionData
    {
        private class SectionDataSerializer : FieldSerializer<SectionData>
        {
            protected override SectionData _Read(BinaryReader reader)
            {
                reader.BaseStream.Position = 1L;
                var compressed = reader.ReadByte() != 0;
                if (compressed)
                {
                    using (var ds = new DeflateStream(reader.BaseStream, CompressionMode.Decompress, true))
                    {
                        using (var br = new BinaryReader(ds))
                        {
                            return deserialize(br);
                        }
                    }
                }
                else
                {
                    reader.BaseStream.Position = 2L;
                    return deserialize(reader);
                }

                SectionData deserialize(BinaryReader br)
                {
                    var data = new SectionData
                    {
                        IsCompressed = compressed,
                        StartX = br.ReadInt32(),
                        StartY = br.ReadInt32(),
                        Width = br.ReadInt16(),
                        Height = br.ReadInt16(),
                    };

                    var totalCount = data.Width * data.Height;
                    // TODO: reuse this list as a buffer
                    var tiles = new List<ComplexTileData>();
                    while (totalCount > 0)
                    {
                        var tile = deserializeTile(br);
                        tiles.Add(tile);
                        totalCount -= tile.Count + 1;
                    }
                    data.Tiles = tiles.ToArray();

                    data.ChestCount = br.ReadInt16();
                    if (data.ChestCount > 8000)
                        throw new Exception("Too many chests!");
                    data.Chests = new ChestData[data.ChestCount];
                    for (int i = 0; i < data.ChestCount; i++)
                    {
                        ref var chest = ref data.Chests[i];
                        chest.ID = br.ReadInt16();
                        chest.TileX = br.ReadInt16();
                        chest.TileY = br.ReadInt16();
                        chest.Name = br.ReadString();
                    }

                    data.SignCount = br.ReadInt16();
                    if (data.SignCount > 1000)
                        throw new Exception("Too many signs!");
                    data.Signs = new SignData[data.SignCount];
                    for (int i = 0; i < data.SignCount; i++)
                    {
                        ref var sign = ref data.Signs[i];
                        sign.ID = br.ReadInt16();
                        sign.TileX = br.ReadInt16();
                        sign.TileY = br.ReadInt16();
                        sign.Text = br.ReadString();
                    }

                    data.TileEntityCount = br.ReadInt16();
                    if (data.TileEntityCount > 1000)
                        throw new Exception("Too many tile entities!");
                    data.TileEntities = new TileEntity[data.TileEntityCount];
                    for (int i = 0; i < data.TileEntityCount; i++)
                    {
                        data.TileEntities[i] = TileEntity.Read(br);
                    }

                    return data;
                }

                ComplexTileData deserializeTile(BinaryReader br)
                {
                    var tile = new ComplexTileData
                    {
                        Flags1 = br.ReadByte()
                    };
                    var flags1 = tile.Flags1;
                    // if HasFlag2 flag is true
                    if (flags1[0])
                    {
                        tile.Flags2 = br.ReadByte();
                        var flags2 = tile.Flags2;
                        // if HasFlag3 flag is true
                        if (flags2[0])
                            tile.Flags3 = br.ReadByte();
                    }
                    var flags3 = tile.Flags3;

                    // if HasTile flag is true
                    if (flags1[1])
                    {
                        // read a byte when this flag is false
                        tile.TileType = flags1[5] ? br.ReadUInt16() : br.ReadByte();

                        if (Constants.tileFrameImportant[tile.TileType])
                        {
                            tile.FrameX = br.ReadInt16();
                            tile.FrameY = br.ReadInt16();
                        }

                        // if HasTileColor flag is true
                        if (flags3[3])
                            tile.TileColor = br.ReadByte();
                    }

                    // if HasWall flag is true
                    if (flags1[2])
                    {
                        tile.WallType = br.ReadByte();
                        // if HasWallColor flag is true
                        if (flags3[4])
                            tile.WallColor = br.ReadByte();
                    }

                    // if Liquid1 or Liquid2 flag is true
                    if (flags1[3] || flags1[4])
                        tile.Liquid = br.ReadByte();

                    // read the additional byte if wall type is big
                    if (flags3[6])
                    {
                        tile.WallType = (ushort)((tile.WallType << 8) | br.ReadByte());
                    }

                    // if HasCountByte or HasCountInt16 flag is true
                    if (flags1[6] || flags1[7])
                    {
                        tile.Count = flags1[7] ? br.ReadInt16() : br.ReadByte();
                    }

                    return tile;
                }
            }
            protected override void _Write(BinaryWriter writer, SectionData data)
            {
                writer.Write(data.IsCompressed);

                if (data.IsCompressed)
                {
                    using (var compressed = new MemoryStream())
                    {
                        using (var ds = new DeflateStream(compressed, CompressionMode.Compress, true))
                        {
                            using (var bw = new BinaryWriter(ds))
                            {
                                serialize(bw);
                            }
                        }
                        writer.Write(compressed.ToArray());
                    }
                }
                else
                {
                    serialize(writer);
                }

                void serialize(BinaryWriter bw)
                {
                    bw.Write(data.StartX);
                    bw.Write(data.StartY);
                    bw.Write(data.Width);
                    bw.Write(data.Height);

                    for (int i = 0; i < data.Tiles.Length; i++)
                    {
                        serializeTile(bw, data.Tiles[i]);
                    }

                    bw.Write(data.ChestCount);
                    for (int i = 0; i < data.ChestCount; i++)
                    {
                        var chest = data.Chests[i];
                        bw.Write(chest.ID);
                        bw.Write(chest.TileX);
                        bw.Write(chest.TileY);
                        bw.Write(chest.Name);
                    }

                    bw.Write(data.SignCount);
                    for (int i = 0; i < data.SignCount; i++)
                    {
                        var sign = data.Signs[i];
                        bw.Write(sign.ID);
                        bw.Write(sign.TileX);
                        bw.Write(sign.TileY);
                        bw.Write(sign.Text);
                    }

                    bw.Write(data.TileEntityCount);
                    for (int i = 0; i < data.TileEntityCount; i++)
                    {
                        TileEntity.Write(bw, data.TileEntities[i]);
                    }
                }

                void serializeTile(BinaryWriter bw, ComplexTileData tile)
                {
                    var flags1 = tile.Flags1;
                    var flags2 = tile.Flags2;
                    var flags3 = tile.Flags3;

                    //flags1[6] = tile.Count > 1;
                    //flags1[7] = tile.Count > byte.MaxValue;

                    bw.Write(flags1);
                    // if HasFlag2 flag is true
                    if (flags1[0])
                    {
                        bw.Write(flags2);
                        // if HasFlag3 flag is true
                        if (flags2[0]) bw.Write(flags3);
                    }

                    // if HasTile flag is true
                    if (flags1[1])
                    {
                        // write a byte when this flag is false
                        if (flags1[5])
                            bw.Write(tile.TileType);
                        else
                            bw.Write((byte)tile.TileType);


                        if (Constants.tileFrameImportant[tile.TileType])
                        {
                            bw.Write(tile.FrameX);
                            bw.Write(tile.FrameY);
                        }

                        // if HasTileColor flag is true
                        if (flags3[3])
                            bw.Write(tile.TileColor);
                    }

                    // if HasWall flag is true
                    if (flags1[2])
                    {
                        bw.Write((byte)tile.WallType);
                        // if HasWallColor flag is true
                        if (flags3[4])
                            bw.Write(tile.WallColor);
                    }

                    // if Liquid1 or Liquid2 flag is true
                    if (flags1[3] || flags1[4])
                        bw.Write(tile.Liquid);

                    // write an additional byte if wall type is greater than byte's max
                    if (flags3[6])
                    {
                        bw.Write((byte)(tile.WallType >> 8));
                    }

                    if (flags1[6] || flags1[7])
                    {
                        if (flags1[7])
                            bw.Write(tile.Count);
                        else
                            bw.Write((byte)tile.Count);
                    }
                }
            }
        }
    }
}
