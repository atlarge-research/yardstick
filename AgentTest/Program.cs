using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using TrProtocol;

namespace AgentTest
{
    class Program
    {
        public static void Tunnel(TcpClient from, TcpClient to, bool fromserver)
        {
            new Thread(() =>
            {
                var f = new PacketSerializer(fromserver);
                var t = new PacketSerializer(!fromserver);
                var br = new BinaryReader(from.GetStream());
                var bw = new BinaryWriter(to.GetStream());
                while (true)
                {
                    var p = f.Deserialize(br);
                    Console.WriteLine((fromserver ? "s2c" : "c2s") + p);
                    bw.Write(t.Serialize(p));
                }
            }).Start();
        }
        static void Main(string[] args)
        {
            var client = new TcpClient();
            var server = new TcpListener(IPAddress.Any, 7777);
            server.Start();
            var client2 = server.AcceptTcpClient();
            client.Connect("yfeil.top", 7777);
            Tunnel(client, client2, true);
            Tunnel(client2, client, false);
        }
    }
}
