using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TrProtocol.Packets.Mobile
{
    public class ServerInfo : Packet
    {
        public override MessageID Type => MessageID.ServerInfo;
        public int ListenPort { get; set; }
        public string WorldName { get; set; }
        public int MaxTilesX { get; set; }
        public bool IsCrimson { get; set; }
        public byte GameMode { get; set; }
        public byte maxNetPlayers { get; set; }
    }
    
    [Serializer(typeof(PrimitiveFieldSerializer<Platform>))]
    public enum Platform : byte // TypeDefIndex: 5205
    {
        None = 0,
        Stadia = 1,
        XBO = 2,
        PSN = 3,
        Editor = 4,
        Nintendo = 5
    }
    
    public class PlayerPlatformInfo : Packet, IPlayerSlot
    {
        public override MessageID Type => MessageID.PlayerPlatformInfo;
        public byte PlayerSlot { get; set; }
        public Platform PlatformId { get; set; }
        public string PlayerId { get; set; }
    }
}
