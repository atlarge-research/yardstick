namespace TrProtocol.Packets.Modules
{
    public class NetCreativePowerPermissionsModule : NetModulesPacket
    {
        public override MessageID Type => MessageID.NetModules;
        public override NetModuleType ModuleType => NetModuleType.NetCreativePowerPermissionsModule;
        public byte AlwaysZero { get; set; } = 0;
        public ushort PowerId { get; set; }
        public byte Level { get; set; }
    }
}