namespace TrProtocol.Packets.Modules;

public class NetTeleportPylonModule : NetModulesPacket
{
    public override MessageID Type => MessageID.NetModules;
    public override NetModuleType ModuleType => NetModuleType.NetTeleportPylonModule;
    public PylonPacketType PylonPacketType { get; set; }
    public ShortPosition Position { get; set; }
    public TeleportPylonType PylonType { get; set; }
}