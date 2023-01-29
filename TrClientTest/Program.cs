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
            var ip = "43.248.184.35";
            ushort port = 1001;
            /*
            ip = "43.248.184.35";
            port = 7777;*/
            var password = "aaaa";
            client.Username = "afftt1";
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
            bool shouldSpam = false;

            client.On<LoadPlayer>(_ =>
                    client.Send(new ClientUUID { UUID = Guid.Empty.ToString() }));
            client.On<WorldData>(_ =>
            {
                if (!shouldSpam)
                {
                    return;
                }
                for (; ; )
                {
                    client.Send(new RequestWorldInfo());
                    client.ChatText("/logout");
                }
            });

            new Thread(() =>
            {
                for (; ; )
                {
                    var t = Console.ReadLine();
                    if (t == "/chatspam") shouldSpam = true;
                    else client.ChatText(t);
                }
            }).Start();

            client.GameLoop(new IPEndPoint(IPAddress.Parse(ip), port), password);
        }
    }
}
