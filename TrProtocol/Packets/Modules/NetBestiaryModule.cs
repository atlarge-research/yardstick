using TrProtocol.Models;

namespace TrProtocol.Packets.Modules
{
    public class NetBestiaryModule : NetModulesPacket
    {
        public override MessageID Type => MessageID.NetModules;
        public override NetModuleType ModuleType => NetModuleType.NetBestiaryModule;
        public byte[] Extra { get; set; }
    }
}