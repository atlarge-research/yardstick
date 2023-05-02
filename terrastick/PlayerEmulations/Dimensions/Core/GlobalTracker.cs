using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Dimensions.Core
{
    public static class GlobalTracker
    {
        private static readonly HashSet<Client> _clients = new();
        
        public static void OnClientConnection(Client client)
        {
            lock (_clients)
            {
                _clients.Add(client);
                client.PacketClient.OnError += _ =>
                {
                    lock (_clients)
                        _clients.Remove(client);
                };
            }
        }

        public static string[] GetClientNames()
        {
            lock (_clients)
                return _clients.Select(c => c.Name).Where(n => n != null).Distinct().ToArray();
        }
    }
}
