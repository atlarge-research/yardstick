using TrProtocol.Models;

namespace TrProtocol.Packets.Modules
{
    public class NetParticlesModule : NetModulesPacket
    {
        public override MessageID Type => MessageID.NetModules;
        public override NetModuleType ModuleType => NetModuleType.NetParticlesModule;
    }
}