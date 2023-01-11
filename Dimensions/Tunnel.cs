using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;
using TrProtocol;

namespace Dimensions
{
    public class Tunnel
    {
        public event Func<Packet, bool>? OnReceive;
        public event Action<Exception>? OnError;
        public event Action? OnClose;
        
        private event Func<Packet> GetData;
        private event Action<Packet> SendData;
        private event Func<bool> Connected;

        private bool shouldStop;
        private string Prefix;
        
        private Tunnel(Func<Packet> getData, Action<Packet> sendData, Func<bool> connected)
        {
            GetData = getData;
            SendData = sendData;
            Connected = connected;
            Task.Run(RunTunnel);
        }
        
        private void RunTunnel()
        {
            try
            {
                while (!shouldStop && Connected())
                {
                    var packet = GetData();
                    if (packet == null) throw new Exception("packet is null");
                    if (OnReceive?.Invoke(packet) ?? true)
                    {
                        Console.WriteLine($"{Prefix}Tunneling: {packet}");
                        SendData(packet);
                    }
                }
            }
            catch (Exception e)
            {
                OnError?.Invoke(e);
            }
            finally
            {
                OnClose?.Invoke();
            }
        }
        
        public static Tunnel CreateS2CTunnel(PacketClient server, PacketClient client)
        {
            return new(() =>
            {
                using var br = new BinaryReader(new MemoryStream(server.Receive()!));
                return Serializers.clientSerializer.Deserialize(br);
            }, p =>
            {
                client.Send(Serializers.serverSerializer.Serialize(p));
            }, () => server.client.Connected && client.client.Connected)
            {
                Prefix = "[S2C] "
            };
        }
        public static Tunnel CreateC2STunnel(PacketClient server, PacketClient client)
        {
            return new(() =>
            {
                using var br = new BinaryReader(new MemoryStream(client.Receive()!));
                return Serializers.serverSerializer.Deserialize(br);
            }, p =>
            {
                 server.Send(Serializers.clientSerializer.Serialize(p));
            }, () => server.client.Connected && client.client.Connected)
            {
                Prefix = "[C2S] "
            };
        }

        public void Close()
        {
            shouldStop = true;
        }
    }
}
