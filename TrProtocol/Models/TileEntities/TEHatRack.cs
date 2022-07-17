namespace TrProtocol.Models.TileEntities;

public partial class TEHatRack : TileEntity
{
    public override TileEntityType EntityType => TileEntityType.TEHatRack;
    public override void WriteExtraData(BinaryWriter writer)
    {
        BitsByte bb = 0;
        bb[0] = Items[0] != null;
        bb[1] = Items[1] != null;
        bb[2] = Dyes[0] != null;
        bb[3] = Dyes[1] != null;
        writer.Write(bb);
        for (int i = 0; i < 2; i++)
        {
            if (Items[i] != null)
                Items[i].Write(writer);
        }
        for (int j = 0; j < 2; j++)
        {
            if (Dyes[j] != null)
                Dyes[j].Write(writer);
        }
    }

    public override TEHatRack ReadExtraData(BinaryReader reader)
    {
        BitsByte bitsByte = reader.ReadByte();
        for (int i = 0; i < 2; i++)
        {
            if (bitsByte[i])
                Items[i] = new ItemData(reader);
        }
        for (int j = 0; j < 2; j++)
        {
            if (bitsByte[j + 2])
                Dyes[j] = new ItemData(reader);
        }
        return this;
    }
    public ItemData[] Items { get; set; } = new ItemData[2];

    public ItemData[] Dyes { get; set; } = new ItemData[2];
}
