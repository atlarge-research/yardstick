using System.Net.Sockets;
using Dimensions.Models;
using TrProtocol;
using TrProtocol.Models;
using TrProtocol.Packets;
using TrProtocol.Packets.Modules;

namespace Dimensions.Core;

public class Client
{
    private readonly PacketClient _client;
    
    private readonly ClientHello clientHello;
    private Tunnel c2s, s2c;
    private PacketClient _serverConnection;
    private Server currentServer;
    private readonly List<ClientHandler> handlers = new ();
    public Server CurrentSever => currentServer;

    public void SendClient(Packet packet)
    {
        Console.WriteLine($"Send To Client: {packet}");
        _client.Send(Serializers.serverSerializer.Serialize(packet));
    }

    public void SendChatMessage(string literal)
    {
        SendClient(new NetTextModuleS2C
        {
            Color = Color.White,
            PlayerSlot = 255,
            Text = NetworkText.FromLiteral(literal)
        });
    }
    
    public void SendServer(Packet packet)
    {
        //Console.WriteLine($"Send To Server: {packet}");
        _serverConnection!.Send(Serializers.clientSerializer.Serialize(packet));
    }

    public Exception Disconnect(string reason)
    {
        SendClient(new Kick { Reason = NetworkText.FromLiteral(reason)});
        //Console.WriteLine($"Disconnected from {_client.client.Client?.RemoteEndPoint}: {reason}");
        _client.client.Close();
        return new(reason);
    }
    
    public Client(TcpClient client)
    {
        _client = new PacketClient(client);

        using var br = new BinaryReader(new MemoryStream(_client.Receive()!));
        
        var packet = Serializers.serverSerializer.Deserialize(br);

        if (packet is not ClientHello hello)
            throw new Exception("ClientHello expected!");
        
        clientHello = hello;

        RegisterHandlers();
    }

    public void TunnelTo(Server server)
    {
        _client.Clear();
        currentServer = server;
        var serverConnection = new TcpClient();
        serverConnection.Connect(server.serverIP!, server.serverPort);
        _serverConnection = new PacketClient(serverConnection);
        
        // prepare the to-server channel to load player state
        _serverConnection.Send(Serializers.clientSerializer.Serialize(clientHello));
        
        s2c = Tunnel.CreateS2CTunnel(_serverConnection, _client);
        s2c.OnReceive += OnS2CPacket;
        s2c.OnError += Console.WriteLine;
        
        c2s = Tunnel.CreateC2STunnel(_serverConnection, _client);
        c2s.OnReceive += OnC2SPacket;
        c2s.OnError += Console.WriteLine;
    }
    

    private void OnCommonPacket(PacketReceiveArgs args)
    {
        foreach (var handler in handlers)
        {
            handler.OnCommonPacket(args);
            if (args.Handled) return;
        }
    }

    private void OnS2CPacket(PacketReceiveArgs args)
    {
        foreach (var handler in handlers)
        {
            handler.OnS2CPacket(args);
            if (args.Handled) return;
        }
        OnCommonPacket(args);
    }

    private void OnC2SPacket(PacketReceiveArgs args)
    {
        foreach (var handler in handlers)
        {
            handler.OnC2SPacket(args);
            if (args.Handled) return;
        }
        OnCommonPacket(args);
    }

    
    // clean existing entities
    private void Cleaning()
    {
        foreach (var handler in handlers)
        {
            handler.OnCleaning();
        }
    }

    public void ChangeServer(Server target)
    {
        if (target == null)
        {
            SendChatMessage("Server not found");
            return;
        }
        
        if (target == currentServer)
        {
            SendChatMessage("Already connected to this server");
            return;
        }
        
        c2s!.OnClose += () =>
        {
            try
            {
                Cleaning();
            }
            catch (Exception e)
            {
                Console.WriteLine(e);
            }
            TunnelTo(target);
        };

        s2c!.Close();
        c2s.Close();

        _client.Cancel();
        _serverConnection!.Cancel();

        _serverConnection.client.Close();

    }

    public void RegisterHandler<T>() where T : ClientHandler, new()
    {
        handlers.Add(new T().SetParent(this));
    }
    
    private void RegisterHandlers()
    {
        RegisterHandler<ConnectionHandler>();
        RegisterHandler<CustomPacketHandler>();
        RegisterHandler<NpcHandler>();
        RegisterHandler<ProjectileHandler>();
        RegisterHandler<PlayerHandler>();
        RegisterHandler<ItemHandler>();
        RegisterHandler<PylonHandler>();
        RegisterHandler<MobileDebugHandler>();
        RegisterHandler<SSCHandler>();
    }
}