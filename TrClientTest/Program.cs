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
            client.CurRelease = "Terraria238";

            client.OnChat += (o, t, c) => Console.WriteLine(t);

            new Thread(() =>
            {
                while (true)
                {
                    client.ChatText(Console.ReadLine());
                }
            }).Start();

            client.GameLoop(new IPEndPoint(IPAddress.Parse("150.138.72.83"), 7777), "123456");
        }
    }
}
