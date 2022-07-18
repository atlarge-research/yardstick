namespace TrProtocol.Packets.Modules
{
    public class NetPingModule : NetModulesPacket
    {
        public override MessageID Type => MessageID.NetModules;
        public override NetModuleType ModuleType => NetModuleType.NetPingModule;
        public Vector2 Position { get; set; }
    }
}