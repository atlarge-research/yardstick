using TrProtocol;
using TrProtocol.Models;
using TrProtocol.Packets;
using TrProtocol.Packets.Modules;

namespace Dimensions.Core;

public class ConnectionHandler : ClientHandler
{

    private SyncPlayer syncPlayer;
    private ShortPosition spawnPosition;
    
    // once client received world data from server, set it to true and request tile data
    private ClientState state = ClientState.New;
    
    public override void OnS2CPacket(PacketReceiveArgs args)
    {
        if (args.Packet is WorldData data)
        {
            if (state != ClientState.ReusedConnect1) return;
            Parent.SendServer(new RequestTileData
            {
                Position = new Position(data.SpawnX, data.SpawnY)
            });
            spawnPosition = new ShortPosition(data.SpawnX, data.SpawnY);
            state = ClientState.ReusedConnect2;
        }
        else if (args.Packet is StartPlaying)
        {
            if (state != ClientState.ReusedConnect2) return;
            var spawn = new SpawnPlayer
            {
                PlayerSlot = syncPlayer.PlayerSlot,
                Context = PlayerSpawnContext.SpawningIntoWorld,
                DeathsPVE = 0,
                DeathsPVP = 0,
                Position = spawnPosition,
                Timer = 0
            };
            Parent.SendClient(spawn);
            Parent.SendServer(spawn);
            state = ClientState.Connected;
        }
    }

    public override void OnC2SPacket(PacketReceiveArgs args)
    {
        if (args.Packet is SyncPlayer sync)
        {
            if (syncPlayer != null && syncPlayer.Name != sync.Name)
            {
                Parent.Disconnect("Name change is not allowed");
                args.Handled = true;
            }

            syncPlayer = sync;
        }
        else if (args.Packet is NetTextModuleC2S text)
        {
            if (text.Text.StartsWith("/server"))
            {
                var target = Program.config.GetServer(text.Text[7..].Trim());
                
                Parent.ChangeServer(target);
            }
        }
    }

    public override void OnCleaning()
    {
        state = ClientState.ReusedConnect1;
    }
}