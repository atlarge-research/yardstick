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
            // createclient(string n);
            // create 10 clients
            // var ip = "127.0.0.1";
            // ushort port = 7777;
            // var password = "";
            // read ip port and password from a yaml file called config.json
            string v = Directory.GetCurrentDirectory();
            var builder = new ConfigurationBuilder()
                .SetBasePath(Directory.GetCurrentDirectory())
                .AddJsonFile("config.json", optional: true, reloadOnChange: true);
            var config = builder.Build();
            var ip = config["ip"];
            ushort port = ushort.Parse(config["port"]);
            var password = config["password"];
            

            for (int i = 0; i < 3; i++)
            {
                // createclient("client" + i);
                // var client = new TClient();
                var client = createclient("client" + i);
                // create client game loop in sepereate thread
                new Thread(() => client.GameLoop(new IPEndPoint(IPAddress.Parse(ip), port), password)).Start();
                // kill thread after 10 seconds
                // Thread.Sleep(10000);
                // client.KillServer();

            }

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
