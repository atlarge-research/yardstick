using System.IO;

namespace TrProtocol.Models
{
    [Serializer(typeof(PlayerDeathReasonSerializer))]
    public partial class PlayerDeathReason
    {
        private partial class PlayerDeathReasonSerializer : FieldSerializer<PlayerDeathReason>
        {
            protected override PlayerDeathReason _Read(BinaryReader br)
            {
                return FromReader(br);
            }

            protected override void _Write(BinaryWriter bw, PlayerDeathReason t)
            {
                t.WriteSelfTo(bw);
            }
        }
    }
}