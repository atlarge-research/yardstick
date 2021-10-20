using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;

namespace TrProtocol.Models
{
    [Serializer(typeof(SectionDataSerializer))]
    public partial struct SectionData
    {
        public static List<int> tileFrameImportant = new()
        {
            3,
            4,
            5,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            21,
            24,
            26,
            27,
            28,
            29,
            31,
            33,
            34,
            35,
            36,
            42,
            49,
            50,
            55,
            61,
            71,
            72,
            73,
            74,
            77,
            78,
            79,
            81,
            82,
            83,
            84,
            85,
            86,
            87,
            88,
            89,
            90,
            91,
            92,
            93,
            94,
            95,
            96,
            97,
            98,
            99,
            100,
            101,
            102,
            103,
            104,
            105,
            106,
            110,
            113,
            114,
            125,
            126,
            128,
            129,
            132,
            133,
            134,
            135,
            136,
            137,
            138,
            139,
            141,
            142,
            143,
            144,
            149,
            165,
            171,
            172,
            173,
            174,
            178,
            184,
            185,
            186,
            187,
            201,
            207,
            209,
            210,
            212,
            215,
            216,
            217,
            218,
            219,
            220,
            227,
            228,
            231,
            233,
            235,
            236,
            237,
            238,
            239,
            240,
            241,
            242,
            243,
            244,
            245,
            246,
            247,
            254,
            269,
            270,
            271,
            275,
            276,
            277,
            278,
            279,
            280,
            281,
            282,
            283,
            285,
            286,
            287,
            288,
            289,
            290,
            291,
            292,
            293,
            294,
            295,
            296,
            297,
            298,
            299,
            300,
            301,
            302,
            303,
            304,
            305,
            306,
            307,
            308,
            309,
            310,
            314,
            316,
            317,
            318,
            319,
            320,
            323,
            324,
            334,
            335,
            337,
            338,
            339,
            349,
            354,
            355,
            356,
            358,
            359,
            360,
            361,
            362,
            363,
            364,
            372,
            373,
            374,
            375,
            376,
            377,
            378,
            380,
            386,
            387,
            388,
            389,
            390,
            391,
            392,
            393,
            394,
            395,
            405,
            406,
            410,
            411,
            412,
            413,
            414,
            419,
            420,
            423,
            424,
            425,
            427,
            428,
            429,
            435,
            436,
            437,
            438,
            439,
            440,
            441,
            442,
            443,
            444,
            445,
            452,
            453,
            454,
            455,
            456,
            457,
            461,
            462,
            463,
            464,
            465,
            466,
            467,
            468,
            469,
            470,
            471,
            475,
            476,
            480,
            484,
            485,
            486,
            487,
            488,
            489,
            490,
            491,
            493,
            494,
            497,
            499,
            505,
            506,
            509,
            510,
            511,
            518,
            519,
            520,
            521,
            522,
            523,
            524,
            525,
            526,
            527,
            529,
            530,
            531,
            532,
            533,
            538,
            542,
            543,
            544,
            545,
            547,
            548,
            549,
            550,
            551,
            552,
            553,
            554,
            555,
            556,
            558,
            559,
            560,
            564,
            565,
            567,
            568,
            569,
            570,
            571,
            572,
            573,
            579,
            580,
            581,
            582,
            583,
            584,
            585,
            586,
            587,
            588,
            589,
            590,
            591,
            592,
            593,
            594,
            595,
            596,
            597,
            598,
            599,
            600,
            601,
            602,
            603,
            604,
            605,
            606,
            607,
            608,
            609,
            610,
            611,
            612,
            613,
            614,
            615,
            616,
            617,
            619,
            620,
            621,
            622,
            623
        };
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

                        if (tileFrameImportant.Contains(tile.TileType))
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


                        if (tileFrameImportant.Contains(tile.TileType))
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
