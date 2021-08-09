using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using TrProtocol;
using TrProtocol.Models;
using TrProtocol.Packets;
using TrProtocol.Packets.Modules;

namespace TrClient
{
    public class TClient
    {
        private TcpClient client;

        public byte PlayerSlot { get; private set; }
        public string CurRelease = "Terraria194";
        public bool IsPlaying { get; private set; }

        private BinaryReader br;
        private BinaryWriter bw;
        private PacketManager mgr = new PacketManager(true);

        public void Connect(IPEndPoint server, IPEndPoint proxy = null)
        {
            if (proxy == null)
            {
                client = new TcpClient();
                client.Connect(server);
                br = new BinaryReader(client.GetStream());
                bw = new BinaryWriter(client.GetStream());
                return;
            }

            client.Connect(proxy);

            //Console.WriteLine("Proxy connected to " + proxy.ToString());
            var encoding = new UTF8Encoding(false, true);
            using (var sw = new StreamWriter(client.GetStream(), encoding, 4096, true) { NewLine = "\r\n" })
            using (var sr = new StreamReader(client.GetStream(), encoding, false, 4096, true))
            {
                sw.WriteLine($"CONNECT {server.ToString()} HTTP/1.1");
                sw.WriteLine("User-Agent: Java/1.8.0_192");
                sw.WriteLine($"Host: {server.ToString()}");
                sw.WriteLine("Accept: text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2");
                sw.WriteLine("Proxy-Connection: keep-alive");
                sw.WriteLine();
                sw.Flush();

                var resp = sr.ReadLine();
                Console.WriteLine("Proxy connection; " + resp);
                if (!resp.StartsWith("HTTP/1.1 200")) throw new Exception();

                while (true)
                {
                    resp = sr.ReadLine();
                    if (string.IsNullOrEmpty(resp)) break;
                }
            }
        }

        public void KillServer()
        {
            client.GetStream().Write(new byte[] { 0, 0 }, 0, 2);
        }
        public Packet Receive()
        {
            return mgr.Deserialize(br);
        }
        public void Send(Packet packet)
        {
            if (packet is IPlayerSlot ips) ips.PlayerSlot = PlayerSlot;
            bw.Write(mgr.Serialize(packet));
        }
        public void Hello(string message)
        {
            Send(new ClientHello { Version = message });
        }

        public void TileGetSection(int x, int y)
        {
            Send(new RequestTileData { Position = new Position { X = x, Y = y } });
        }

        public void Spawn(short x, short y)
        {
            Send(new SpawnPlayer
            {
                Position = new ShortPosition { X = x, Y = y },
                Context = PlayerSpawnContext.SpawningIntoWorld
            });
        }

        public void SendPlayer()
        {
            Send(new SyncPlayer
            {
                Name = "rabbit2"
            });
            Send(new PlayerHealth { StatLifeMax = 100, StatLife = 100 });
            for (byte i = 0; i < 73; ++i)
                Send(new SyncEquipment { ItemSlot = i });
        }

        public void ChatText(string message)
        {
            Send(new NetTextModuleC2S
            {
                Command = "Say",
                Text = message
            });
        }

        public delegate void OnStatusBarCallback(TClient self, NetworkText text);
        public event OnStatusBarCallback OnStatusBar;
        public delegate void OnChatCallback(TClient self, string text, Color color);
        public event OnChatCallback OnChat;

        public void GameLoop(IPEndPoint endPoint, string password, IPEndPoint proxy = null)
        {
            Connect(endPoint, proxy);
            Console.WriteLine("Sending Client Hello...");
            Hello(CurRelease);

            /*TcpClient verify = new TcpClient();
            byte[] raw = Encoding.ASCII.GetBytes("-1551487326");
            verify.Connect(new IPEndPoint(endPoint.Address, 7980));
            verify.GetStream().Write(raw, 0, raw.Length);
            verify.Close();*/

            bool connected = true;
            while (connected)
            {
                Packet packet = Receive();
                try
                {
                    //lock (Console.Out) Console.WriteLine($"received type {packet.Type}");
                    switch (packet)
                    {
                        case StatusText status:
                            OnStatusBar?.Invoke(this, status.Text);
                            break;
                        case NetTextModuleS2C text:
                            OnChat?.Invoke(this, text.Text, text.Color);
                            break;
                        case SmartTextMessage text:
                            OnChat?.Invoke(this, text.Text.ToString(), text.Color);
                            break;
                        case Kick kick:
                            Console.WriteLine("Kicked : " + kick.Reason.ToString());
                            connected = false;
                            break;
                        case LoadPlayer player:
                            PlayerSlot = player.PlayerSlot;
                            SendPlayer();
                            Send(new RequestWorldInfo());
                            Console.WriteLine("Requesting World Info...");
                            break;
                        case WorldData data:
                            Packet worldInfo = packet;
                            if (!IsPlaying)
                            {
                                TileGetSection(100, 100);
                                IsPlaying = true;
                            }
                            break;
                        case StartPlaying:
                            Console.WriteLine("Spawning player...");
                            Spawn(100, 100);
                            break;
                        default:
                            //Console.ForegroundColor = ConsoleColor.Red;
                            //Console.WriteLine($"[Warning] unknown packet type {packet.Type}");
                            //Console.ResetColor();
                            break;
                    }
                }
                catch (Exception e)
                {
                    Console.ForegroundColor = ConsoleColor.Red;
                    Console.WriteLine($"Exception caught when trying to parse packet {packet.Type}");
                    Console.WriteLine(e);
                    Console.ResetColor();
                }
            }

            client.Close();

        }
    }
}