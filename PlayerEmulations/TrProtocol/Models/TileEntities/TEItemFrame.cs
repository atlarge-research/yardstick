namespace TrProtocol.Models.TileEntities;

public partial class TEItemFrame : TileEntity
{
    public override TileEntityType EntityType => TileEntityType.TEItemFrame;
    public override void WriteExtraData(BinaryWriter writer)
    {
        Item.Write(writer);
    }

    public override TEItemFrame ReadExtraData(BinaryReader reader)
    {
        Item = new(reader);
        return this;
    }
    public ItemData Item { get; set; }
}
