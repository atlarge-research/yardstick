using TrProtocol.Models;

namespace TrProtocol.Packets.Modules
{
    [C2SOnly]
    public class NetTextModuleC2S : NetModulesPacket
    {
        public override MessageID Type => MessageID.NetModules;
        public override short ModuleType => 1;
        public string Command { get; set; }
        public string Text { get; set; }
    }
    [S2COnly]
    public class NetTextModuleS2C : NetModulesPacket, IPlayerSlot
    {
        public override MessageID Type => MessageID.NetModules;
        public override short ModuleType => 1;
        public byte PlayerSlot { get; set; }
        public NetworkText Text { get; set; }
        public Color Color { get; set; }
    }
}
