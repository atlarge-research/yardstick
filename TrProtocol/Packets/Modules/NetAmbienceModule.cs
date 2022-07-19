namespace TrProtocol.Packets.Modules
{
    public class NetAmbienceModule : NetModulesPacket, IPlayerSlot
    {
        public override MessageID Type => MessageID.NetModules;
        public override NetModuleType ModuleType => NetModuleType.NetAmbienceModule;
        public byte PlayerSlot { get; set; }
        public int Random { get; set; }
        public SkyEntityType SkyType { get; set; }
    }
}