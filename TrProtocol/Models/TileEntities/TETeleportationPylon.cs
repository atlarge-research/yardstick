namespace TrProtocol.Models.TileEntities;

public partial class TETeleportationPylon : TileEntity
{
    public override TileEntityType EntityType => TileEntityType.TETeleportationPylon;

    public override TileEntity ReadExtraData(BinaryReader reader)
    {
        return this;
    }

    public override void WriteExtraData(BinaryWriter writer)
    {
    }
}
