using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using TrProtocol;
using TrProtocol.Packets;
using TrProtocol.Packets.Modules;

namespace TrProtocolTest
{
    class Program
    {
        static void Main(string[] args)
        {
            var mgr = new PacketManager();
            using var ms = new MemoryStream();
            using var bw = new BinaryWriter(ms);
            var b = mgr.Serialize(new ClientHello
            {
                Version = "Terraria183"
            });
            Console.WriteLine(string.Join(" ", b.Select(b => $"{b:x2}")));
            var p = mgr.Deserialize(new BinaryReader(new MemoryStream(mgr.Serialize(new NetTextModule
            {
                Command = "say",
                Text = "text",
            }))));
            var p2 = mgr.Deserialize(new BinaryReader(new MemoryStream(mgr.Serialize(new TileSection
            {
                Data = new byte[] { 1, 2, 3, 4, 5, 6 }
            }))));
            var p3 = mgr.Deserialize(new BinaryReader(new MemoryStream(mgr.Serialize(new TileChange
            {
                Position = new TrProtocol.Models.ShortPosition { X = 2, Y = 4}
            }))));

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
