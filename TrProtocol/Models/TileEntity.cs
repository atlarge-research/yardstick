using TrProtocol.Models.TileEntities;

namespace TrProtocol.Models;

[Serializer(typeof(TileEntitySerializer))]
public abstract partial class TileEntity
{
    private static readonly Dictionary<TileEntityType, Type> tileEntityDict = new()
    {
        { TileEntityType.TETrainingDummy, typeof(TETrainingDummy) },
        { TileEntityType.TEItemFrame, typeof(TEItemFrame) },
        { TileEntityType.TELogicSensor, typeof(TELogicSensor) },
        { TileEntityType.TEDisplayDoll, typeof(TEDisplayDoll) },
        { TileEntityType.TEWeaponsRack, typeof(TEWeaponsRack) },
        { TileEntityType.TEHatRack, typeof(TEHatRack) },
        { TileEntityType.TEFoodPlatter, typeof(TEFoodPlatter) },
        { TileEntityType.TETeleportationPylon, typeof(TETeleportationPylon) }
    };
    public static TileEntity Read(BinaryReader br)
    {
        var type = (TileEntityType)br.ReadByte();
        if (tileEntityDict.TryGetValue(type, out var t))
        {
            var entity = Activator.CreateInstance(t) as TileEntity;
            entity.ID = br.ReadInt32();
            entity.Position = new() { X = br.ReadInt16(), Y = br.ReadInt16() };
            entity.ReadExtraData(br);
            return entity;
        }
        else
            return null;
    }
    public static void Write(BinaryWriter bw, TileEntity t)
    {
        bw.Write((byte)t.EntityType);
        bw.Write(t.ID);
        bw.Write(t.Position.X);
        bw.Write(t.Position.Y);
        t.WriteExtraData(bw);
    }
    public abstract TileEntityType EntityType { get; }
    public ShortPosition Position { get; set; }
    public int ID { get; set; }
    public abstract void WriteExtraData(BinaryWriter writer);
    public abstract TileEntity ReadExtraData(BinaryReader reader);
}
