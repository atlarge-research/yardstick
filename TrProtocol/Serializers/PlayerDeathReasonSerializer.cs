namespace TrProtocol.Models;

[Serializer(typeof(PlayerDeathReasonSerializer))]
public partial class PlayerDeathReason
{
    private class PlayerDeathReasonSerializer : FieldSerializer<PlayerDeathReason>
    {
        protected override PlayerDeathReason ReadOverride(BinaryReader br)
        {
            return FromReader(br);
        }

        protected override void WriteOverride(BinaryWriter bw, PlayerDeathReason t)
        {
            t.WriteSelfTo(bw);
        }
    }
}