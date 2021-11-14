using System;
using System.Net;
using System.Threading;
using TrClient;

namespace TrClientTest
{
    class Program
    {
        static void Main(string[] args)
        {
            var client = new TClient();
            Console.Write("ip>");
            var ip = Console.ReadLine();
            Console.Write("port>");
            var port = ushort.Parse(Console.ReadLine());
            Console.Write("password>");
            var password = Console.ReadLine();
            Console.Write("curRelaese>");
            client.CurRelease = Console.ReadLine();
            Console.Write("username>");
            client.Username = Console.ReadLine();

            client.OnChat += (o, t, c) => Console.WriteLine(t);

            new Thread(() =>
            {
                while (true)
                {
                    client.ChatText(Console.ReadLine());
                }
            }).Start();

            client.GameLoop(new IPEndPoint(IPAddress.Parse(ip), port), password);
        }
    }
}
