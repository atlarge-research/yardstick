using System.Collections.Concurrent;
using System.Net.Sockets;

namespace Dimensions.Core
{
    public class PacketClient
    {
        private readonly NetworkStream stream;
        private readonly BlockingCollection<byte[]> packets = new();
        public event Action<Exception> OnError = Console.WriteLine;
        private readonly BinaryReader br;
        private readonly BinaryWriter bw;

        public readonly TcpClient client;
        
        public PacketClient(TcpClient client)
        {
            this.client = client;
            stream = client.GetStream();
            br = new(stream);
            bw = new(stream);

            Task.Run(ListenThread);
        }

        public void Cancel()
        {
            packets.Add(null);
        }

        public void Clear()
        {
            while (packets.TryTake(out _)) ;
        }
        
        public byte[] Receive()
        {
            var b = packets.Take();
            return b;
        }

        public void Send(byte[] data)
        {
            lock (bw) bw.Write(data);
        }
        
        private void ListenThread()
        {
            try
            {
                for (;;)
                {
                    var size = br.ReadUInt16();
                    var buf = new byte[size];
                    Buffer.BlockCopy(br.ReadBytes(size - 2), 0, buf, 2, size - 2);
                    buf[0] = (byte)(size & 0xFF);
                    buf[1] = (byte)(size >> 8);
                    packets.Add(buf);
                }
            }
            catch (Exception e)
            {
                OnError?.Invoke(e);
            }
        }
    }
}
