namespace TrProtocol.Models;

public abstract partial class TileEntity
{
    public class TileEntitySerializer : FieldSerializer<TileEntity>
    {
        protected override TileEntity ReadOverride(BinaryReader br)
        {
            return TileEntity.Read(br, true);
        }

        protected override void WriteOverride(BinaryWriter bw, TileEntity t)
        {
            TileEntity.Write(bw, t, true);
        }
    }
}
