using System;
using System.Net;
using System.Threading;
using TrClient;
using TrProtocol.Models;
using TrProtocol.Packets;
using TrProtocol.Packets.Modules;

namespace TrClientTest
{
    class Program
    {
        static void Main(string[] args)
        {
            var client = new TClient();
            var ip = "127.0.0.1";
            ushort port = 7777;
            /*
            ip = "43.248.184.35";
            port = 7777;*/
            var password = "aaaa";
            client.Username = "afftt";
            /*
            Console.Write("ip>");
            var ip = Console.ReadLine();
            Console.Write("port>");
            var port = ushort.Parse(Console.ReadLine());
            Console.Write("password>");
            var password = Console.ReadLine();
            Console.Write("username>");
            client.Username = Console.ReadLine();*/

            client.OnChat += (o, t, c) => Console.WriteLine(t);
            client.OnMessage += (o, t) => Console.WriteLine(t);
            
            new Thread(() =>
            {
                while (true)
                {
                    client.ChatText(Console.ReadLine());
                    client.Send(new NetTeleportPylonModule
                    {
                        Position = new ShortPosition(1000, 1000),
                        PylonPacketType = PylonPacketType.PylonWasAdded,
                        PylonType = TeleportPylonType.Victory
                    });
                }
            }).Start();

            client.GameLoop(new IPEndPoint(IPAddress.Parse(ip), port), password);
        }
    }
}
