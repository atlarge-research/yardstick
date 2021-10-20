using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Channels;

namespace TrProtocol.Models
{
    [Serializer(typeof(LiquidDataSerializer))]
    public partial struct LiquidData
    {
        private class LiquidDataSerializer : FieldSerializer<LiquidData>
        {
            protected override LiquidData _Read(BinaryReader br)
            {
                var liquid = new LiquidData()
                {
                    TotalChanges = br.ReadUInt16()
                };
                var changes = new List<LiquidChange>();
                for (int i = 0; i < liquid.TotalChanges; i++)
                {
                    changes.Add(new LiquidChange()
                    {
                        Position = new(br.ReadInt16(), br.ReadInt16()),
                        LiquidAmount = br.ReadByte(),
                        LiquidType = br.ReadByte()
                    });
                }
                liquid.LiquidChanges = changes.ToArray();
                return liquid;
            }

            protected override void _Write(BinaryWriter bw, LiquidData t)
{
                bw.Write(t.TotalChanges);
                foreach (LiquidChange change in t.LiquidChanges)
                {
                    bw.Write(change.Position.X);
                    bw.Write(change.Position.Y);
                    bw.Write(change.LiquidAmount);
                    bw.Write(change.LiquidType);
                }
            }
        }
    }
}
