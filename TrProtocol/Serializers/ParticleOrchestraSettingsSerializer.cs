using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using TrProtocol.Models;

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
