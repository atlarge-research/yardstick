namespace TrProtocol.Packets.Modules
{
    public class NetTextModule : NetModulesPacket
    {
        public override MessageID Type => MessageID.NetModules;
        public override short ModuleType => 1;
        public string Command { get; set; }
        public string Text { get; set; }
    }
}
