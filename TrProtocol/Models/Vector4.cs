namespace TrProtocol.Models
{
    // Token: 0x0200086B RID: 2155
    public struct Vector4
    {
        // Token: 0x1700051E RID: 1310
        // (get) Token: 0x060039CE RID: 14798 RVA: 0x00599B48 File Offset: 0x00597D48
        public static Vector4 One => Vector4._one;

        // Token: 0x1700051F RID: 1311
        // (get) Token: 0x060039CF RID: 14799 RVA: 0x00599B50 File Offset: 0x00597D50
        public static Vector4 Zero => Vector4._zero;

        // Token: 0x060039D0 RID: 14800 RVA: 0x00599B58 File Offset: 0x00597D58
        public Vector4(float x, float y, float z, float w)
        {
            X = x;
            Y = y;
            Z = z;
            W = w;
        }

        // Token: 0x060039D1 RID: 14801 RVA: 0x00599B78 File Offset: 0x00597D78
        public Vector4(Vector2 value, float z, float w)
        {
            X = value.X;
            Y = value.Y;
            Z = z;
            W = w;
        }

        // Token: 0x060039D2 RID: 14802 RVA: 0x00599BA4 File Offset: 0x00597DA4
        public Vector4(Vector3 value, float w)
        {
            X = value.X;
            Y = value.Y;
            Z = value.Z;
            W = w;
        }

        // Token: 0x060039D3 RID: 14803 RVA: 0x00599BD4 File Offset: 0x00597DD4
        public Vector4(float value)
        {
            W = value;
            Z = value;
            Y = value;
            X = value;
        }

        // Token: 0x060039D4 RID: 14804 RVA: 0x00599C04 File Offset: 0x00597E04
        public static Vector4 Lerp(Vector4 value1, Vector4 value2, float amount)
        {
            Vector4 result;
            result.X = value1.X + (value2.X - value1.X) * amount;
            result.Y = value1.Y + (value2.Y - value1.Y) * amount;
            result.Z = value1.Z + (value2.Z - value1.Z) * amount;
            result.W = value1.W + (value2.W - value1.W) * amount;
            return result;
        }

        // Token: 0x060039D5 RID: 14805 RVA: 0x00599C8C File Offset: 0x00597E8C
        public static void Lerp(ref Vector4 value1, ref Vector4 value2, float amount, out Vector4 result)
        {
            result.X = value1.X + (value2.X - value1.X) * amount;
            result.Y = value1.Y + (value2.Y - value1.Y) * amount;
            result.Z = value1.Z + (value2.Z - value1.Z) * amount;
            result.W = value1.W + (value2.W - value1.W) * amount;
        }

        // Token: 0x060039D6 RID: 14806 RVA: 0x00599D0C File Offset: 0x00597F0C
        public static Vector4 operator -(Vector4 value)
        {
            Vector4 result;
            result.X = -value.X;
            result.Y = -value.Y;
            result.Z = -value.Z;
            result.W = -value.W;
            return result;
        }

        // Token: 0x060039D7 RID: 14807 RVA: 0x00599D58 File Offset: 0x00597F58
        public static Vector4 operator *(Vector4 value1, Vector4 value2)
        {
            Vector4 result;
            result.X = value1.X * value2.X;
            result.Y = value1.Y * value2.Y;
            result.Z = value1.Z * value2.Z;
            result.W = value1.W * value2.W;
            return result;
        }

        // Token: 0x060039D8 RID: 14808 RVA: 0x00599DBC File Offset: 0x00597FBC
        public static Vector4 operator *(Vector4 value1, float scaleFactor)
        {
            Vector4 result;
            result.X = value1.X * scaleFactor;
            result.Y = value1.Y * scaleFactor;
            result.Z = value1.Z * scaleFactor;
            result.W = value1.W * scaleFactor;
            return result;
        }

        // Token: 0x060039D9 RID: 14809 RVA: 0x00599E0C File Offset: 0x0059800C
        public static Vector4 operator *(float scaleFactor, Vector4 value1)
        {
            Vector4 result;
            result.X = value1.X * scaleFactor;
            result.Y = value1.Y * scaleFactor;
            result.Z = value1.Z * scaleFactor;
            result.W = value1.W * scaleFactor;
            return result;
        }

        // Token: 0x060039DA RID: 14810 RVA: 0x00599E5C File Offset: 0x0059805C
        public static Vector4 operator /(Vector4 value1, Vector4 value2)
        {
            return new Vector4
            {
                X = value1.X / value2.X,
                Y = value1.Y / value2.Y,
                Z = value1.Z / value2.Z,
                W = value1.W / value2.W
            };
        }

        // Token: 0x060039DB RID: 14811 RVA: 0x00599EC8 File Offset: 0x005980C8
        public static Vector4 operator /(Vector4 value1, float divider)
        {
            float num = 1f / divider;
            return new Vector4
            {
                X = value1.X * num,
                Y = value1.Y * num,
                Z = value1.Z * num,
                W = value1.W * num
            };
        }

        // Token: 0x060039DC RID: 14812 RVA: 0x00599F28 File Offset: 0x00598128
        public bool Equals(Vector4 other)
        {
            return X == other.X && Y == other.Y && Z == other.Z && W == other.W;
        }

        // Token: 0x060039DD RID: 14813 RVA: 0x00599F78 File Offset: 0x00598178
        public override bool Equals(object obj)
        {
            bool flag = obj is Vector4;
            bool result;
            if (flag)
            {
                Vector4 p = (Vector4)obj;
                result = (this == p);
            }
            else
            {
                result = false;
            }
            return result;
        }

        // Token: 0x060039DE RID: 14814 RVA: 0x00599FB0 File Offset: 0x005981B0
        public override int GetHashCode()
        {
            return X.GetHashCode() + Y.GetHashCode() + Z.GetHashCode() + W.GetHashCode();
        }

        // Token: 0x060039DF RID: 14815 RVA: 0x00599FF4 File Offset: 0x005981F4
        public static bool operator ==(Vector4 p1, Vector4 p2)
        {
            return p1.X == p2.X && p1.Y == p2.Y && p1.Z == p2.Z && p1.W == p2.W;
        }

        // Token: 0x060039E0 RID: 14816 RVA: 0x0059A044 File Offset: 0x00598244
        public static bool operator !=(Vector4 p1, Vector4 p2)
        {
            return p1.X != p2.X || p1.Y != p2.Y || p1.Z != p2.Z || p1.W != p2.W;
        }

        // Token: 0x060039E1 RID: 14817 RVA: 0x0059A094 File Offset: 0x00598294
        public static Vector4 operator +(Vector4 p1, Vector4 p2)
        {
            Vector4 result;
            result.X = p1.X + p2.X;
            result.Y = p1.Y + p2.Y;
            result.Z = p1.Z + p2.Z;
            result.W = p1.W + p2.W;
            return result;
        }

        // Token: 0x060039E2 RID: 14818 RVA: 0x0059A0F8 File Offset: 0x005982F8
        public static Vector4 operator -(Vector4 p1, Vector4 p2)
        {
            Vector4 result;
            result.X = p1.X - p2.X;
            result.Y = p1.Y - p2.Y;
            result.Z = p1.Z - p2.Z;
            result.W = p1.W - p2.W;
            return result;
        }

        // Token: 0x060039E3 RID: 14819 RVA: 0x0059A15C File Offset: 0x0059835C
        public static Vector4 Max(Vector4 value1, Vector4 value2)
        {
            return new Vector4
            {
                X = ((value1.X > value2.X) ? value1.X : value2.X),
                Y = ((value1.Y > value2.Y) ? value1.Y : value2.Y),
                Z = ((value1.Z > value2.Z) ? value1.Z : value2.Z),
                W = ((value1.W > value2.W) ? value1.W : value2.W)
            };
        }

        // Token: 0x060039E4 RID: 14820 RVA: 0x0059A204 File Offset: 0x00598404
        public static void Max(ref Vector4 value1, ref Vector4 value2, out Vector4 result)
        {
            result.X = ((value1.X > value2.X) ? value1.X : value2.X);
            result.Y = ((value1.Y > value2.Y) ? value1.Y : value2.Y);
            result.Z = ((value1.Z > value2.Z) ? value1.Z : value2.Z);
            result.W = ((value1.W > value2.W) ? value1.W : value2.W);
        }

        // Token: 0x040061DE RID: 25054
        public static Vector4[] Array;

        // Token: 0x040061DF RID: 25055
        public float W;

        // Token: 0x040061E0 RID: 25056
        public float X;

        // Token: 0x040061E1 RID: 25057
        public float Y;

        // Token: 0x040061E2 RID: 25058
        public float Z;

        // Token: 0x040061E3 RID: 25059
        private static Vector4 _zero = default(Vector4);

        // Token: 0x040061E4 RID: 25060
        private static readonly Vector4 _one = new Vector4(1f, 1f, 1f, 1f);
    }
}
