using System;
using System.IO;
using System.Net;
using System.Threading;
using TrClient;
using TrProtocol.Models;
using TrProtocol.Packets;
using TrProtocol.Packets.Modules;
using Microsoft.Extensions.Configuration;

namespace TrClientTest
{
    class Program
    {




        static void Main(string[] args)
        {
            string ip = "127.0.0.1";
            ushort port = 7777;
            string password = "";
            // read ip port and password from a yaml file called config.json
            // if it exists

            string v = Directory.GetCurrentDirectory();
            var builder = new ConfigurationBuilder()
                .SetBasePath(Directory.GetCurrentDirectory())
                .AddJsonFile("config.json", optional: true, reloadOnChange: true);
            if(File.Exists("config.json"))
            {
                var config = builder.Build();
                ip = config["ip"];
                port = ushort.Parse(config["port"]);
                password = config["password"];
            }
  
            var client = createclient("BOT");


            new Thread(() => client.GameLoop(new IPEndPoint(IPAddress.Parse(ip), port), password)).Start();

            // after 5 seconds teleport the client to 10 blocks to the right of spawn
            // Thread.Sleep(5000);
            // short delta  = 10;
            // client.TeleportPlayer(client.currentX - delta, client.currentY);


        }

        private static TClient createclient(string name)
        {
            var client = new TClient();

            client.Username = name;

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
                }

            });
            // run the game loop in a separate thread


            return client;
        }
    }
}
