namespace TrProtocol.Packets.Modules
{
    public class NetCreativeUnlocksPlayerReportModule : NetModulesPacket
    {
        public override MessageID Type => MessageID.NetModules;
        public override NetModuleType ModuleType => NetModuleType.NetCreativeUnlocksPlayerReportModule;
        public byte AlwaysZero { get; set; } = 0;
        public short ItemId { get; set; }
        public ushort Count { get; set; }
    }
}