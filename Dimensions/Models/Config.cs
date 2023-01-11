using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Dimensions.Models;

public class Config
{
    public ushort listenPort;
    public string protocolVersion;
    public Server[] servers;

    private Dictionary<string, Server>? _serverCache;

    public Server? GetServer(string name)
    {
        _serverCache ??= servers.ToDictionary(s => s.name!, s => s);
        return _serverCache.TryGetValue(name, out var val) ? val : null;
    }
}