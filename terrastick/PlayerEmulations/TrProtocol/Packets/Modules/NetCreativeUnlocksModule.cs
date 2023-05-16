namespace TrProtocol.Packets.Modules;

public class NetCreativeUnlocksModule : NetModulesPacket
{
    public override MessageID Type => MessageID.NetModules;
    public override NetModuleType ModuleType => NetModuleType.NetCreativeUnlocksModule;
    public short ItemId { get; set; }
    public ushort Count { get; set; }
}