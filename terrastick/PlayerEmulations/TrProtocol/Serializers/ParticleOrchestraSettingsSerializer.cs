namespace TrProtocol.Models;

[Serializer(typeof(ParticleOrchestraSettingsSerializer))]
public partial class ParticleOrchestraSettings
{
    private class ParticleOrchestraSettingsSerializer : FieldSerializer<ParticleOrchestraSettings>
    {
        protected override ParticleOrchestraSettings ReadOverride(BinaryReader br)
        {
            return DeserializeFrom(br);
        }

        protected override void WriteOverride(BinaryWriter bw, ParticleOrchestraSettings t)
        {
            t.Serialize(bw);
        }
    }
}
