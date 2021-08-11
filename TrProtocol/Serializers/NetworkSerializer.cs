using System.IO;

namespace TrProtocol.Models
{
	[Serializer(typeof(NetworkSerializer))]
	public partial class NetworkText
	{
        private class NetworkSerializer : FieldSerializer<NetworkText>
		{
			protected override NetworkText _Read(BinaryReader br)
			{
				return Deserialize(br);
			}

			protected override void _Write(BinaryWriter bw, NetworkText t)
			{
				t.Serialize(bw);
			}
		}
	}
}
