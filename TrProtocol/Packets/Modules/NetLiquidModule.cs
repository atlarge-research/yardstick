using TrProtocol.Models;

namespace TrProtocol.Packets.Modules
{
    public class NetLiquidModule : NetModulesPacket
    {
        public override MessageID Type => MessageID.NetModules;
        public override NetModuleType ModuleType => NetModuleType.NetLiquidModule;
        public ushort Count { get; set; }
        public byte[] Changes { get; set; }
    }
}