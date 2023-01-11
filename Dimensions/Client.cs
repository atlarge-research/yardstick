using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;
using Dimensions.Models;
using TrProtocol;
using TrProtocol.Models;
using TrProtocol.Packets;
using TrProtocol.Packets.Modules;

namespace Dimensions;

public enum ClientState
{
    New,
    ReusedConnect1,
    ReusedConnect2,
    Connected,
}
public class Client
{
    
    private readonly PacketClient _client;
    
    private readonly ClientHello clientHello;
    private SyncPlayer? syncPlayer;
    private Tunnel? c2s, s2c;
    private PacketClient? _serverConnection;
    private Server? currentServer;

    private ShortPosition spawnPosition;
    
    // once client received world data from server, set it to true and request tile data
    private ClientState state;
    
    public void Send(Packet packet)
    {
        _client.Send(Serializers.serverSerializer.Serialize(packet));
    }
    
    public Exception Disconnect(string reason)
    {
        Send(new Kick { Reason = NetworkText.FromLiteral(reason)});
        Console.WriteLine($"Disconnected from {_client.client.Client?.RemoteEndPoint}: {reason}");
        _client.client.Close();
        return new(reason);
    }
    
    public Client(TcpClient client)
    {
        _client = new PacketClient(client){useDebug = true};

        using var br = new BinaryReader(new MemoryStream(_client.Receive()!));
        
        var packet = Serializers.serverSerializer.Deserialize(br);

        if (packet is not ClientHello hello)
            throw Disconnect("Expected ClientHello");

        clientHello = hello;
        state = ClientState.New;
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

    private bool OnS2CPacket(Packet packet)
    {
        switch (packet)
        {
            case WorldData data:
                if (state == ClientState.ReusedConnect1)
                {
                    _serverConnection!.Send(
                        Serializers.clientSerializer.Serialize(new RequestTileData
                        {
                            Position = new Position(data.SpawnX, data.SpawnY)
                        }));
                    spawnPosition = new ShortPosition(data.SpawnX, data.SpawnY);
                    state = ClientState.ReusedConnect2;
                }

                break;
            case StartPlaying:
                if (state == ClientState.ReusedConnect2)
                {
                    var spawn = new SpawnPlayer
                    {
                        PlayerSlot = syncPlayer.PlayerSlot,
                        Context = PlayerSpawnContext.SpawningIntoWorld,
                        DeathsPVE = 0,
                        DeathsPVP = 0,
                        Position = spawnPosition,
                        Timer = 0
                    };
                    _client.Send(Serializers.serverSerializer.Serialize(spawn));
                    _serverConnection!.Send(Serializers.clientSerializer.Serialize(spawn));

                    state = ClientState.Connected;
                }
                break;
        }
        return true;
    }

    // clean existing entities
    private void Cleaning()
    {

    }

    private bool OnC2SPacket(Packet packet)
    {
        switch (packet)
        {
            case SyncPlayer sync:
                if (syncPlayer != null && syncPlayer.Name != sync.Name)
                {
                    Disconnect("Name change is not allowed");
                    return false;
                }
                syncPlayer = sync;
                break;
            case NetTextModuleC2S text:
                if (text.Command == "Say" && text.Text.StartsWith("/server"))
                {
                    var target = Program.config.GetServer(text.Text[7..].Trim());
                    if (target == null)
                    {
                        Send(new NetTextModuleS2C
                        {
                            PlayerSlot = 255,
                            Text = NetworkText.FromLiteral("Server not found"),
                            Color = Color.White,
                        });
                    }
                    else if (target == currentServer)
                    {
                        Send(new NetTextModuleS2C
                        {
                            PlayerSlot = 255,
                            Text = NetworkText.FromLiteral("Already connected to this server"),
                            Color = Color.White,
                        });
                    }
                    else
                    {
                        // we need to close s2c first to ensure the client doesn't receive a half packet
                        c2s!.OnClose += () =>
                        {
                            Cleaning();
                            state = ClientState.ReusedConnect1;
                            TunnelTo(target);
                        };
                        
                        s2c!.Close();
                        c2s.Close();

                        _client.Cancel();
                        _serverConnection!.Cancel();

                        _serverConnection.client.Close();

                        return false;
                    }
                }
                break;
        }

        return true;
    }
}