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
    Reused,
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
        _client = new PacketClient(client);

        using var br = new BinaryReader(new MemoryStream(_client.Receive()!));
        
        var packet = Serializers.serverSerializer.Deserialize(br);

        if (packet is not ClientHello hello)
            throw Disconnect("Expected ClientHello");

        clientHello = hello;
        state = ClientState.New;
    }

    public void TunnelTo(Server server)
    {
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
                if (state == ClientState.Reused)
                {
                    _serverConnection!.Send(
                        Serializers.clientSerializer.Serialize(new RequestTileData
                        {
                            Position = new Position(data.SpawnX, data.SpawnY)
                        }));
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
                if (syncPlayer == null)
                {
                    syncPlayer = sync;
                    break;
                }

                if (syncPlayer.Name != sync.Name)
                {
                    Disconnect("Name change is not allowed");
                    return false;
                }
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
                        s2c!.OnClose += () =>
                        {
                            c2s!.OnClose += () =>
                            {
                                Cleaning();
                                state = ClientState.Reused;
                                TunnelTo(target);
                            };
                            c2s.Close();
                            _client.Cancel();
                        };
                        s2c.Close();
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