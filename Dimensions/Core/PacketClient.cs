using System.Collections.Concurrent;
using System.Net.Sockets;
using TrProtocol;

namespace Dimensions.Core
{
    public class PacketClient
    {
        private readonly BlockingCollection<Packet> packets = new();
        public event Action<Exception> OnError = Console.WriteLine;
        private readonly BinaryReader br;
        private readonly BinaryWriter bw;

        public readonly TcpClient client;

        private readonly PacketSerializer serializer;
        public PacketClient(TcpClient client, bool isClient)
        {
            this.client = client;
            var stream = client.GetStream();
            br = new(stream);
            bw = new(stream);

            serializer = isClient ? Serializers.serverSerializer : Serializers.clientSerializer;
            Task.Run(ListenThread);
        }

        public void Cancel()
        {
            OnError?.Invoke(new Exception($"PacketClient {client.Client.RemoteEndPoint} cancel called"));
            packets.Add(null);
        }

        public void Clear()
        {
            while (packets.TryTake(out _)) ;
        }
        
        public Packet Receive()
        {
            var b = packets.Take();
            return b;
        }

        public void Send(Packet data)
        {
            //Console.WriteLine($"Send=>{client.Client.RemoteEndPoint}: {data}");
            lock (bw) bw.Write(serializer.Serialize(data));
        }
        
        private void ListenThread()
        {
            try
            {
                for (;;)
                {
                    var packet = serializer.Deserialize(br);
                    packets.Add(packet);
                }
            }
            catch (Exception e)
            {
                OnError?.Invoke(e);
            }
        }
    }
}
