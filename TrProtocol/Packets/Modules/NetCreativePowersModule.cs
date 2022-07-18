namespace TrProtocol.Packets.Modules
{
    public class NetCreativePowersModule : NetModulesPacket
    {
        public override MessageID Type => MessageID.NetModules;
        public override NetModuleType ModuleType => NetModuleType.NetCreativePowersModule;
        public CreativePowerTypes PowerType { get; set; }
        public byte[] Extra { get; set; }
    }
}