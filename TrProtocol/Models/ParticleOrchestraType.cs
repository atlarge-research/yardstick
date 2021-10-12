using TrProtocol.Serializers;

namespace TrProtocol.Models
{
    [Serializer(typeof(ByteEnumSerializer<ParticleOrchestraType>))]
    public enum ParticleOrchestraType : byte
    {
        Keybrand,
        FlameWaders,
        StellarTune,
        WallOfFleshGoatMountFlames,
        BlackLightningHit,
        RainbowRodHit,
        BlackLightningSmall,
        StardustPunch,
        PrincessWeapon
    }
}
