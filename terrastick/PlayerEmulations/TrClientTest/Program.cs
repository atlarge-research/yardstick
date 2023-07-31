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
            string workload = "TEL";
            // name is botname and last 5 characters of hostname
            // randomize name
            string name = "BOT_" + Environment.MachineName.Substring(Environment.MachineName.Length - 5)+ "_" + new Random().Next(0,100);
            string logpath = "terrastick_bot_logs";
            int workload_duration = 300;

            if (Environment.GetEnvironmentVariable("TERRASTICK_IP") != null)
            {
                ip = Environment.GetEnvironmentVariable("TERRASTICK_IP");
            }
            if(Environment.GetEnvironmentVariable("TERRASTICK_WORKLOAD") != null)
            {
                workload = Environment.GetEnvironmentVariable("TERRASTICK_WORKLOAD");

            }
            if(Environment.GetEnvironmentVariable("TERRASTICK_USERNAME") != null)
            {
                name = Environment.GetEnvironmentVariable("TERRASTICK_USERNAME");

            }
            if(Environment.GetEnvironmentVariable("TERRASTICK_LOGPATH") != null)
            {
                logpath = Environment.GetEnvironmentVariable("TERRASTICK_LOGPATH");

            }
            if(Environment.GetEnvironmentVariable("TERRASTICK_WORKLOAD_DURATION") !=null)
            {
                workload_duration = int.Parse(Environment.GetEnvironmentVariable("TERRASTICK_WORKLOAD_DURATION"));
            }
            Console.WriteLine("IP: " + ip);
            ushort port = 7777;
            string password = "";


            var client = createclient(name, workload,workload_duration);


            new Thread(() => client.GameLoop(new IPEndPoint(IPAddress.Parse(ip), port), password)).Start();

        }

        private static TClient createclient(string name,string workload,int workload_duration)
        {
            var client = new TClient(workload,workload_duration);

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
