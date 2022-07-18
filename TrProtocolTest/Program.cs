using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using TrProtocol;
using TrProtocol.Packets;

namespace TrProtocolTest
{
    class Program
    {
        static void Main(string[] args)
        {
            var mgr = new PacketSerializer(true);
            using var ms = new MemoryStream();
            using var bw = new BinaryWriter(ms);

            try
            {
                _ = new PacketSerializer(true, "Terraria238");
            }
            catch (Exception e)
            {
                Console.WriteLine(e);
            }

            var b = mgr.Serialize(new ClientHello
            {
                Version = "Terraria183"
            });
            Console.WriteLine(string.Join(" ", b.Select(b => $"{b:x2}")));
            var p2 = mgr.Deserialize(new BinaryReader(new MemoryStream(mgr.Serialize(new TileSection
            {
                Data = new()
                {
                    IsCompressed = true,
                    StartX = 0,
                    StartY = 0,
                    Width = 10,
                    Height = 10,
                    Tiles = new TrProtocol.Models.ComplexTileData[100],
                    SignCount = 1,
                    Signs = new TrProtocol.Models.SignData[] { new() { TileX = 0, TileY = 0, ID = 0, Text = "TestSign" } },
                    ChestCount = 1,
                    Chests = new TrProtocol.Models.ChestData[] { new() { TileX = 0, TileY = 0, ID = 0, Name = "TestChest" } },
                    TileEntityCount = 8,
                    TileEntities = new TrProtocol.Models.TileEntity[]
                    {
                        new TrProtocol.Models.TileEntities.TEDisplayDoll()
                        {
                            ID = 0,
                            Position = new TrProtocol.Models.ShortPosition { X = 0, Y = 0 }
                        },
                        new TrProtocol.Models.TileEntities.TEFoodPlatter()
                        {
                            ID = 1,
                            Position = new TrProtocol.Models.ShortPosition { X = 1, Y = 1 },
                            Item = new()
                            {
                                ItemID = 757,
                                Stack = 1
                            }
                        },
                        new TrProtocol.Models.TileEntities.TEHatRack()
                        {
                            ID = 2,
                            Position = new TrProtocol.Models.ShortPosition { X = 2, Y = 2 },
                            Items = new TrProtocol.Models.ItemData[]
                            {
                                new()
                                {
                                    ItemID = 757,
                                    Stack = 1
                                },
                                new()
                                {
                                    ItemID = 757,
                                    Stack = 1
                                }
                            },
                            Dyes = new TrProtocol.Models.ItemData[]
                            {
                                new()
                                {
                                    ItemID = 757,
                                    Stack = 1
                                },
                                new()
                                {
                                    ItemID = 757,
                                    Stack = 1
                                }
                            }
                        },
                        new TrProtocol.Models.TileEntities.TEItemFrame()
                        {
                            ID = 3,
                            Position = new TrProtocol.Models.ShortPosition { X = 3, Y = 3 },
                            Item = new()
                                {
                                    ItemID = 757,
                                    Stack = 1
                                }
                        },
                        new TrProtocol.Models.TileEntities.TELogicSensor()
                        {
                            ID = 4,
                            Position = new TrProtocol.Models.ShortPosition { X = 4, Y = 4 },
                            LogicCheck = TrProtocol.Models.LogicCheckType.None,
                            On = true
                        },
                        new TrProtocol.Models.TileEntities.TETeleportationPylon()
                        {
                            ID = 5,
                            Position = new TrProtocol.Models.ShortPosition { X = 5, Y = 5 },
                        },
                        new TrProtocol.Models.TileEntities.TETrainingDummy()
                        {
                            ID = 6,
                            Position = new TrProtocol.Models.ShortPosition { X = 6, Y = 6 },
                            NPC = 1
                        },
                        new TrProtocol.Models.TileEntities.TEWeaponsRack()
                        {
                            ID = 7,
                            Position = new TrProtocol.Models.ShortPosition { X = 7, Y = 7 },
                            Item = new()
                                {
                                    ItemID = 757,
                                    Stack = 1
                                }
                        }
                    }
                }
            }))));
            var p3 = mgr.Deserialize(new BinaryReader(new MemoryStream(mgr.Serialize(new TileChange
            {
                Position = new TrProtocol.Models.ShortPosition { X = 2, Y = 4 }
            }))));

            try
            {
                mgr.Serialize(new SyncProjectile()
                {
                    ProjType = short.MaxValue
                });
            }
            catch (Exception e)
            {
                Console.WriteLine(e);
            }
            var sw = Stopwatch.StartNew();

            for (int i = 0; i < 1000000; ++i)
            {
                mgr.Serialize(new TileChange
                {
                    Position = new TrProtocol.Models.ShortPosition { X = 2, Y = 4 }
                });
            }

            Console.WriteLine($"serialize cost: {sw.ElapsedMilliseconds / 1000f:f2}us");

            sw = Stopwatch.StartNew();

            var ms2 = new MemoryStream(mgr.Serialize(new TileChange
            {
                Position = new TrProtocol.Models.ShortPosition { X = 2, Y = 4 }
            }));
            var br = new BinaryReader(ms2);

            for (int i = 0; i < 1000000; ++i)
            {
                br.BaseStream.Position = 0;
                mgr.Deserialize(br);
            }

            Console.WriteLine($"deserialize cost: {sw.ElapsedMilliseconds / 1000f:f2}us");
        }
    }
}
