using System;

namespace TrProtocol.Models
{
    internal static class HalfUtils
    {
        // Token: 0x060040EE RID: 16622 RVA: 0x005CC360 File Offset: 0x005CA560
        public static ushort Pack(float value)
        {
            uint num = BitConverter.ToUInt32(BitConverter.GetBytes(value));
            uint num2 = (num & 2147483648u) >> 16;
            uint num3 = num & 2147483647u;
            bool flag = num3 > 1207955455u;
            ushort result;
            if (flag)
            {
                result = (ushort)(num2 | 32767u);
            }
            else
            {
                bool flag2 = num3 < 947912704u;
                if (flag2)
                {
                    uint num4 = (num3 & 8388607u) | 8388608u;
                    int num5 = (int)(113u - (num3 >> 23));
                    num3 = ((num5 > 31) ? 0u : (num4 >> num5));
                    result = (ushort)(num2 | num3 + 4095u + (num3 >> 13 & 1u) >> 13);
                }
                else
                {
                    result = (ushort)(num2 | num3 + 3355443200u + 4095u + (num3 >> 13 & 1u) >> 13);
                }
            }
            return result;
        }

        // Token: 0x060040EF RID: 16623 RVA: 0x005CC418 File Offset: 0x005CA618
        public static float Unpack(ushort value)
        {
            bool flag = ((int)value & -33792) == 0;
            uint num3;
            if (flag)
            {
                bool flag2 = (value & 1023) > 0;
                if (flag2)
                {
                    uint num = 4294967282u;
                    uint num2 = (uint)(value & 1023);
                    while ((num2 & 1024u) == 0u)
                    {
                        num -= 1u;
                        num2 <<= 1;
                    }
                    num2 &= 4294966271u;
                    num3 = (uint)((int)(value & 32768) << 16 | (int)((int)(num + 127u) << 23) | (int)((int)num2 << 13));
                }
                else
                {
                    num3 = (uint)((uint)(value & 32768) << 16);
                }
            }
            else
            {
                num3 = (uint)((int)(value & 32768) << 16 | (value >> 10 & 31) - 15 + 127 << 23 | (int)(value & 1023) << 13);
            }

            return BitConverter.ToSingle(BitConverter.GetBytes(num3));
        }

        // Token: 0x0400676B RID: 26475
        public const int cFracBits = 10;

        // Token: 0x0400676C RID: 26476
        public const int cExpBits = 5;

        // Token: 0x0400676D RID: 26477
        public const int cSignBit = 15;

        // Token: 0x0400676E RID: 26478
        public const uint cSignMask = 32768u;

        // Token: 0x0400676F RID: 26479
        public const uint cFracMask = 1023u;

        // Token: 0x04006770 RID: 26480
        public const int cExpBias = 15;

        // Token: 0x04006771 RID: 26481
        public const uint cRoundBit = 4096u;

        // Token: 0x04006772 RID: 26482
        public const uint eMax = 16u;

        // Token: 0x04006773 RID: 26483
        public const int eMin = -14;

        // Token: 0x04006774 RID: 26484
        public const uint wMaxNormal = 1207955455u;

        // Token: 0x04006775 RID: 26485
        public const uint wMinNormal = 947912704u;

        // Token: 0x04006776 RID: 26486
        public const uint BiasDiffo = 3355443200u;

        // Token: 0x04006777 RID: 26487
        public const int cFracBitsDiff = 13;
    }
}