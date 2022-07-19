namespace TrProtocol.Packets.Modules
{
    [C2SOnly]
    public class NetTextModuleC2S : NetModulesPacket
    {
        public override MessageID Type => MessageID.NetModules;
        public override NetModuleType ModuleType => NetModuleType.NetTextModule;
        public string Command { get; set; }
        public string Text { get; set; }
        public override string ToString()
        {
            return $"[C2S] {Text}";
        }
    }
}
