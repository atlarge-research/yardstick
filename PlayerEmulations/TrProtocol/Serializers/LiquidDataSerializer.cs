namespace TrProtocol.Models;

[Serializer(typeof(LiquidDataSerializer))]
public partial struct LiquidData
{
	private class LiquidDataSerializer : FieldSerializer<LiquidData>
	{
		protected override LiquidData ReadOverride(BinaryReader br)
		{
			var liquid = new LiquidData()
			{
				TotalChanges = br.ReadUInt16()
			};
			var changes = new LiquidChange[liquid.TotalChanges];
			for (int i = 0; i < liquid.TotalChanges; i++)
			{
				changes[i] = new LiquidChange()
				{
					Position = new(br.ReadInt16(), br.ReadInt16()),
					LiquidAmount = br.ReadByte(),
					LiquidType = (LiquidType)br.ReadByte()
				};
			}
			liquid.LiquidChanges = changes;
			return liquid;
		}

		protected override void WriteOverride(BinaryWriter bw, LiquidData t)
		{
			bw.Write(t.TotalChanges);
			foreach (LiquidChange change in t.LiquidChanges)
			{
				bw.Write(change.Position.X);
				bw.Write(change.Position.Y);
				bw.Write(change.LiquidAmount);
				bw.Write((byte)change.LiquidType);
			}
		}
	}
}
