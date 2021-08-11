using System;

namespace TrProtocol.Models
{
	// Token: 0x0200096E RID: 2414
    public struct HalfVector2 : IPackedVector<uint>, IPackedVector, IEquatable<HalfVector2>
    {
        public uint PackedValue
        {
            get
            {
                return this.packedValue;
            }
            set
            {
                this.packedValue = value;
            }
        }

        // Token: 0x060040F2 RID: 16626 RVA: 0x005CC4FC File Offset: 0x005CA6FC
        public HalfVector2(float x, float y)
        {
            this.packedValue = HalfVector2.PackHelper(x, y);
        }

        // Token: 0x060040F3 RID: 16627 RVA: 0x005CC50C File Offset: 0x005CA70C
        public HalfVector2(Vector2 vector)
        {
            this.packedValue = HalfVector2.PackHelper(vector.X, vector.Y);
        }

        // Token: 0x060040F4 RID: 16628 RVA: 0x005CC528 File Offset: 0x005CA728
        public void PackFromVector4(Vector4 vector)
        {
            this.packedValue = HalfVector2.PackHelper(vector.X, vector.Y);
        }

        // Token: 0x060040F5 RID: 16629 RVA: 0x005CC544 File Offset: 0x005CA744
        public static uint PackHelper(float vectorX, float vectorY)
        {
            uint num = (uint)HalfUtils.Pack(vectorX);
            uint num2 = (uint)((uint)HalfUtils.Pack(vectorY) << 16);
            return num | num2;
        }

        // Token: 0x060040F6 RID: 16630 RVA: 0x005CC56C File Offset: 0x005CA76C
        public Vector2 ToVector2()
        {
            Vector2 result;
            result.X = HalfUtils.Unpack((ushort)this.packedValue);
            result.Y = HalfUtils.Unpack((ushort)(this.packedValue >> 16));
            return result;
        }

        // Token: 0x060040F7 RID: 16631 RVA: 0x005CC5A8 File Offset: 0x005CA7A8
        public Vector4 ToVector4()
        {
            Vector2 vector = this.ToVector2();
            return new Vector4(vector.X, vector.Y, 0f, 1f);
        }

        // Token: 0x060040F8 RID: 16632 RVA: 0x005CC5DC File Offset: 0x005CA7DC
        public override string ToString()
        {
            return this.ToVector2().ToString();
        }

        // Token: 0x060040F9 RID: 16633 RVA: 0x005CC604 File Offset: 0x005CA804
        public override int GetHashCode()
        {
            return this.packedValue.GetHashCode();
        }

        // Token: 0x060040FA RID: 16634 RVA: 0x005CC624 File Offset: 0x005CA824
        public override bool Equals(object obj)
        {
            return obj is HalfVector2 && this.Equals((HalfVector2)obj);
        }

        // Token: 0x060040FB RID: 16635 RVA: 0x005CC650 File Offset: 0x005CA850
        public bool Equals(HalfVector2 other)
        {
            return this.packedValue.Equals(other.packedValue);
        }

        // Token: 0x060040FC RID: 16636 RVA: 0x005CC674 File Offset: 0x005CA874
        public static bool operator ==(HalfVector2 a, HalfVector2 b)
        {
            return a.Equals(b);
        }

        // Token: 0x060040FD RID: 16637 RVA: 0x005CC690 File Offset: 0x005CA890
        public static bool operator !=(HalfVector2 a, HalfVector2 b)
        {
            return !a.Equals(b);
        }

        // Token: 0x04006778 RID: 26488
        public uint packedValue;
    }
}