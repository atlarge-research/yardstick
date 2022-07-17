namespace TrProtocol.Models.TileEntities;

public partial class TELogicSensor : TileEntity
{
    public override TileEntityType EntityType => TileEntityType.TELogicSensor;
    public override void WriteExtraData(BinaryWriter writer)
    {
        writer.Write((byte)LogicCheck);
        writer.Write(On);
    }
    public override TELogicSensor ReadExtraData(BinaryReader reader)
    {
        LogicCheck = (LogicCheckType)reader.ReadByte();
        On = reader.ReadBoolean();
        return this;
    }
    public LogicCheckType LogicCheck { get; set; }
    public bool On { get; set; }
}
