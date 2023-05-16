namespace TrProtocol.Models;

public partial class ItemData
{
    public ItemData(BinaryReader br)
    {
        Read(br);
    }
    public ItemData() { }
    public override string ToString()
    {
        return $"[{ItemID}, {Prefix}, {Stack}]";
    }
    public void Write(BinaryWriter bw)
    {
        bw.Write(ItemID);
        bw.Write(Prefix);
        bw.Write(Stack);
    }
    public ItemData Read(BinaryReader br)
    {
        ItemID = br.ReadInt16();
        Prefix = br.ReadByte();
        Stack = br.ReadInt16();
        return this;
    }
    public short ItemID { get; set; }
    public byte Prefix { get; set; }
    public short Stack { get; set; }
}
