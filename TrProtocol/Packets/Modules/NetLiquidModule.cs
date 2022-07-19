namespace TrProtocol.Packets.Modules
{
    public class NetLiquidModule : NetModulesPacket
    {
        public override MessageID Type => MessageID.NetModules;
        public override NetModuleType ModuleType => NetModuleType.NetLiquidModule;
        public LiquidData LiquidChanges { get; set; }
    }
}