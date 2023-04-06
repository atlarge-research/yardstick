namespace TrProtocol.Models;

[Serializer(typeof(NetworkSerializer))]
public partial class NetworkText
{
    private class NetworkSerializer : FieldSerializer<NetworkText>
    {
        protected override NetworkText ReadOverride(BinaryReader br)
        {
            return Deserialize(br);
        }

        protected override void WriteOverride(BinaryWriter bw, NetworkText t)
        {
            t.Serialize(bw);
        }
    }
}
