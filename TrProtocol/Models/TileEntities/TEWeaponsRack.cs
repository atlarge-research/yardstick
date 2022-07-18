namespace TrProtocol.Models.TileEntities;

public partial class TEWeaponsRack : TileEntity
{
    public override TileEntityType EntityType => TileEntityType.TEWeaponsRack;
    public override void WriteExtraData(BinaryWriter writer)
    {
        Item.Write(writer);
    }

    public override TEWeaponsRack ReadExtraData(BinaryReader reader)
    {
        Item = new(reader);
        return this;
    }
    public ItemData Item { get; set; }
}
