using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;

namespace Dimensions
{
    public class Listener
    {
        private readonly TcpListener listener;
        public event Action<Exception>? OnError;
        
        public Listener(IPEndPoint ep)
        {
            listener = new TcpListener(ep);
            listener.Start();
        }

        private void OnAcceptClient(TcpClient client)
        {
            var @default = Program.config.servers.First();
            try
            {
                new Client(client).TunnelTo(@default);
            }
            catch (Exception e)
            {
                OnError?.Invoke(e);
            }
        }
        public void ListenThread()
        {
            for (;;)
            {
                try
                {
                    var client = listener.AcceptTcpClient();
                    Console.WriteLine($"Accepted connection from {client.Client.RemoteEndPoint}");
                    Task.Run(() => OnAcceptClient(client));
                }
                catch (Exception e)
                {
                    Console.WriteLine($"Error accepting connection: {e}");
                }
            }
        }
    }
}
