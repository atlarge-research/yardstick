namespace TrProtocol.Packets.Modules;

public class NetParticlesModule : NetModulesPacket
{
    public override MessageID Type => MessageID.NetModules;
    public override NetModuleType ModuleType => NetModuleType.NetParticlesModule;
    public ParticleOrchestraType ParticleType { get; set; }
    public ParticleOrchestraSettings Setting { get; set; }
}