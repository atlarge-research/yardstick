using Dimensions.Models;
using TrProtocol;

namespace Dimensions.Core
{
    public class Tunnel
    {
        public event Action<PacketReceiveArgs> OnReceive;
        public event Action<Exception>? OnError;
        public event Action? OnClose;

        private readonly PacketClient source, target;

        private bool shouldStop;
        private string prefix;
        
        public Tunnel(PacketClient source, PacketClient target, string prefix)
        {
            this.source = source;
            this.target = target;
            this.prefix = prefix;
            Task.Run(RunTunnel);
        }
        
        private void RunTunnel()
        {
            try
            {
                while (!shouldStop && source.client.Connected && target.client.Connected)
                {
                    var packet = source.Receive();
                    if (packet == null) throw new Exception("packet is null");
                    var args = new PacketReceiveArgs(packet);
                    OnReceive?.Invoke(args);
                    if (args.Handled) continue;
                    //Console.WriteLine($"{Prefix}Tunneling: {packet}");
                    target.Send(packet);
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
        
        public void Close()
        {
            shouldStop = true;
        }
    }
}
