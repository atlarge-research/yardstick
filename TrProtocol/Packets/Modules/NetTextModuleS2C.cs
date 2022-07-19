namespace TrProtocol.Packets.Modules
{
    [S2COnly]
    public class NetTextModuleS2C : NetModulesPacket, IPlayerSlot
    {
        public override MessageID Type => MessageID.NetModules;
        public override NetModuleType ModuleType => NetModuleType.NetTextModule;
        public byte PlayerSlot { get; set; }
        public NetworkText Text { get; set; }
        public Color Color { get; set; }
        public override string ToString()
        {
            return $"[S2C] {Text._text}";
        }
    }
}