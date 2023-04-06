namespace TrProtocol.Models.TileEntities;

public partial class TEDisplayDoll : TileEntity
{
    public override void WriteExtraData(BinaryWriter writer)
    {
        BitsByte bb = 0;
        bb[0] = Items[0] != null;
        bb[1] = Items[1] != null;
        bb[2] = Items[2] != null;
        bb[3] = Items[3] != null;
        bb[4] = Items[4] != null;
        bb[5] = Items[5] != null;
        bb[6] = Items[6] != null;
        bb[7] = Items[7] != null;
        BitsByte bb2 = 0;
        bb2[0] = Dyes[0] != null;
        bb2[1] = Dyes[1] != null;
        bb2[2] = Dyes[2] != null;
        bb2[3] = Dyes[3] != null;
        bb2[4] = Dyes[4] != null;
        bb2[5] = Dyes[5] != null;
        bb2[6] = Dyes[6] != null;
        bb2[7] = Dyes[7] != null;
        writer.Write(bb);
        writer.Write(bb2);
        for (int i = 0; i < 8; i++)
        {
            ItemData item = Items[i];
            if (item != null)
            {
                item.Write(writer);
            }
        }
        for (int j = 0; j < 8; j++)
        {
            ItemData item = Dyes[j];
            if (item != null)
            {
                item.Write(writer);
            }
        }
    }
    public override TEDisplayDoll ReadExtraData(BinaryReader reader)
    {
        BitsByte bitsByte = reader.ReadByte();
        BitsByte bitsByte2 = reader.ReadByte();
        for (int i = 0; i < 8; i++)
        {
            if (bitsByte[i])
            {
                Items[i] = new ItemData(reader);
            }
        }
        for (int j = 0; j < 8; j++)
        {
            if (bitsByte2[j])
            {
                Dyes[j] = new ItemData(reader);
            }
        }
        return this;
    }
    public override TileEntityType EntityType => TileEntityType.TEDisplayDoll;
    public ItemData[] Items { get; set; } = new ItemData[8];
    public ItemData[] Dyes { get; set; } = new ItemData[8];
}
