using System.IO;

namespace TrProtocol.Models
{
    [Serializer(typeof(ParticleOrchestraSettingsSerializer))]
    public partial class ParticleOrchestraSettings
    {
        private class ParticleOrchestraSettingsSerializer : FieldSerializer<ParticleOrchestraSettings>
        {
            protected override ParticleOrchestraSettings _Read(BinaryReader br)
            {
                return DeserializeFrom(br);
            }

            protected override void _Write(BinaryWriter bw, ParticleOrchestraSettings t)
            {
                t.Serialize(bw);
            }
        }
    }
}
