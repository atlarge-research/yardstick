﻿using System;
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

            if (Environment.GetEnvironmentVariable("TERRARIA_IP") != null)
            {
                ip = Environment.GetEnvironmentVariable("TERRARIA_IP");
            }
            
            Console.WriteLine("IP: " + ip);
            ushort port = 7777;
            string password = "";


            var client = createclient("BOT");


            new Thread(() => client.GameLoop(new IPEndPoint(IPAddress.Parse(ip), port), password)).Start();

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
