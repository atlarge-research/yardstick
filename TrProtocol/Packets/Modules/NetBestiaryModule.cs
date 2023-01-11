namespace TrProtocol.Packets.Modules;

public class NetBestiaryModule : NetModulesPacket
{
    public override MessageID Type => MessageID.NetModules;
    public override NetModuleType ModuleType => NetModuleType.NetBestiaryModule;
    public BestiaryUnlockType UnlockType { get; set; }
    public short NPCType { get; set; }
    private bool __shouldSerializeKillCount
        => UnlockType == BestiaryUnlockType.Kill;
    [Condition(nameof(__shouldSerializeKillCount))]
    public ushort KillCount { get; set; }
}