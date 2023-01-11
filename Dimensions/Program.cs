
using System.Net;
using System.Text.Json.Serialization;
using Dimensions.Models;
using Newtonsoft.Json;

namespace Dimensions;

public static class Program
{
    public static readonly Config config;
    
    static Program()
    {
        config = JsonConvert.DeserializeObject<Config>(File.ReadAllText("config.json"))!;
    }

    public static void Main(string[] args)
    {
        var listener = new Listener(new(IPAddress.Any, config.listenPort));
        listener.ListenThread();
    }
}