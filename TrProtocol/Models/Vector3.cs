using System;
using System.Globalization;

namespace TrProtocol.Models
{
    // Token: 0x0200086A RID: 2154
    public struct Vector3 : IEquatable<Vector3>
    {
        // Token: 0x17000513 RID: 1299
        // (get) Token: 0x0600397C RID: 14716 RVA: 0x005978B8 File Offset: 0x00595AB8
        public static Vector3 Zero => Vector3._zero;

        // Token: 0x17000514 RID: 1300
        // (get) Token: 0x0600397D RID: 14717 RVA: 0x005978D0 File Offset: 0x00595AD0
        public static Vector3 One => Vector3._one;

        // Token: 0x17000515 RID: 1301
        // (get) Token: 0x0600397E RID: 14718 RVA: 0x005978E8 File Offset: 0x00595AE8
        public static Vector3 UnitX => Vector3._unitX;

        // Token: 0x17000516 RID: 1302
        // (get) Token: 0x0600397F RID: 14719 RVA: 0x00597900 File Offset: 0x00595B00
        public static Vector3 UnitY => Vector3._unitY;

        // Token: 0x17000517 RID: 1303
        // (get) Token: 0x06003980 RID: 14720 RVA: 0x00597918 File Offset: 0x00595B18
        public static Vector3 UnitZ => Vector3._unitZ;

        // Token: 0x17000518 RID: 1304
        // (get) Token: 0x06003981 RID: 14721 RVA: 0x00597930 File Offset: 0x00595B30
        public static Vector3 Up => Vector3._up;

        // Token: 0x17000519 RID: 1305
        // (get) Token: 0x06003982 RID: 14722 RVA: 0x00597948 File Offset: 0x00595B48
        public static Vector3 Down => Vector3._down;

        // Token: 0x1700051A RID: 1306
        // (get) Token: 0x06003983 RID: 14723 RVA: 0x00597960 File Offset: 0x00595B60
        public static Vector3 Right => Vector3._right;

        // Token: 0x1700051B RID: 1307
        // (get) Token: 0x06003984 RID: 14724 RVA: 0x00597978 File Offset: 0x00595B78
        public static Vector3 Left => Vector3._left;

        // Token: 0x1700051C RID: 1308
        // (get) Token: 0x06003985 RID: 14725 RVA: 0x00597990 File Offset: 0x00595B90
        public static Vector3 Forward => Vector3._forward;

        // Token: 0x1700051D RID: 1309
        // (get) Token: 0x06003986 RID: 14726 RVA: 0x005979A8 File Offset: 0x00595BA8
        public static Vector3 Backward => Vector3._backward;

        // Token: 0x06003987 RID: 14727 RVA: 0x005979C0 File Offset: 0x00595BC0
        public Vector3(float x, float y, float z)
        {
            X = x;
            Y = y;
            Z = z;
        }

        // Token: 0x06003988 RID: 14728 RVA: 0x005979D8 File Offset: 0x00595BD8
        public Vector3(float value)
        {
            Z = value;
            Y = value;
            X = value;
        }

        // Token: 0x06003989 RID: 14729 RVA: 0x005979F0 File Offset: 0x00595BF0
        public Vector3(Vector2 value, float z)
        {
            X = value.X;
            Y = value.Y;
            Z = z;
        }

        // Token: 0x0600398A RID: 14730 RVA: 0x00597A14 File Offset: 0x00595C14
        public override string ToString()
        {
            CultureInfo currentCulture = CultureInfo.CurrentCulture;
            return string.Format(currentCulture, "{{X:{0} Y:{1} Z:{2}}}", new object[]
            {
                X.ToString(currentCulture),
                Y.ToString(currentCulture),
                Z.ToString(currentCulture)
            });
        }

        // Token: 0x0600398B RID: 14731 RVA: 0x00597A6C File Offset: 0x00595C6C
        public bool Equals(Vector3 other)
        {
            return X == other.X && Y == other.Y && Z == other.Z;
        }

        // Token: 0x0600398C RID: 14732 RVA: 0x00597AAC File Offset: 0x00595CAC
        public override bool Equals(object obj)
        {
            bool result = false;
            bool flag = obj is Vector3;
            if (flag)
            {
                result = Equals((Vector3)obj);
            }
            return result;
        }

        // Token: 0x0600398D RID: 14733 RVA: 0x00597AE0 File Offset: 0x00595CE0
        public override int GetHashCode()
        {
            return X.GetHashCode() + Y.GetHashCode() + Z.GetHashCode();
        }

        // Token: 0x0600398E RID: 14734 RVA: 0x00597B18 File Offset: 0x00595D18
        public float Length()
        {
            float num = X * X + Y * Y + Z * Z;
            return (float)Math.Sqrt(num);
        }

        // Token: 0x0600398F RID: 14735 RVA: 0x00597B5C File Offset: 0x00595D5C
        public float LengthSquared()
        {
            return X * X + Y * Y + Z * Z;
        }

        // Token: 0x06003990 RID: 14736 RVA: 0x00597B98 File Offset: 0x00595D98
        public static float Distance(Vector3 value1, Vector3 value2)
        {
            float num = value1.X - value2.X;
            float num2 = value1.Y - value2.Y;
            float num3 = value1.Z - value2.Z;
            float num4 = num * num + num2 * num2 + num3 * num3;
            return (float)Math.Sqrt(num4);
        }

        // Token: 0x06003991 RID: 14737 RVA: 0x00597BEC File Offset: 0x00595DEC
        public static void Distance(ref Vector3 value1, ref Vector3 value2, out float result)
        {
            float num = value1.X - value2.X;
            float num2 = value1.Y - value2.Y;
            float num3 = value1.Z - value2.Z;
            float num4 = num * num + num2 * num2 + num3 * num3;
            result = (float)Math.Sqrt(num4);
        }

        // Token: 0x06003992 RID: 14738 RVA: 0x00597C3C File Offset: 0x00595E3C
        public static float DistanceSquared(Vector3 value1, Vector3 value2)
        {
            float num = value1.X - value2.X;
            float num2 = value1.Y - value2.Y;
            float num3 = value1.Z - value2.Z;
            return num * num + num2 * num2 + num3 * num3;
        }

        // Token: 0x06003993 RID: 14739 RVA: 0x00597C84 File Offset: 0x00595E84
        public static void DistanceSquared(ref Vector3 value1, ref Vector3 value2, out float result)
        {
            float num = value1.X - value2.X;
            float num2 = value1.Y - value2.Y;
            float num3 = value1.Z - value2.Z;
            result = num * num + num2 * num2 + num3 * num3;
        }

        // Token: 0x06003994 RID: 14740 RVA: 0x00597CCC File Offset: 0x00595ECC
        public static float Dot(Vector3 vector1, Vector3 vector2)
        {
            return vector1.X * vector2.X + vector1.Y * vector2.Y + vector1.Z * vector2.Z;
        }

        // Token: 0x06003995 RID: 14741 RVA: 0x00597D08 File Offset: 0x00595F08
        public static void Dot(ref Vector3 vector1, ref Vector3 vector2, out float result)
        {
            result = vector1.X * vector2.X + vector1.Y * vector2.Y + vector1.Z * vector2.Z;
        }

        // Token: 0x06003996 RID: 14742 RVA: 0x00597D38 File Offset: 0x00595F38
        public void Normalize()
        {
            float num = X * X + Y * Y + Z * Z;
            float num2 = 1f / (float)Math.Sqrt(num);
            X *= num2;
            Y *= num2;
            Z *= num2;
        }

        // Token: 0x06003997 RID: 14743 RVA: 0x00597DAC File Offset: 0x00595FAC
        public static Vector3 Normalize(Vector3 value)
        {
            float num = value.X * value.X + value.Y * value.Y + value.Z * value.Z;
            float num2 = 1f / (float)Math.Sqrt(num);
            Vector3 result;
            result.X = value.X * num2;
            result.Y = value.Y * num2;
            result.Z = value.Z * num2;
            return result;
        }

        // Token: 0x06003998 RID: 14744 RVA: 0x00597E28 File Offset: 0x00596028
        public static void Normalize(ref Vector3 value, out Vector3 result)
        {
            float num = value.X * value.X + value.Y * value.Y + value.Z * value.Z;
            float num2 = 1f / (float)Math.Sqrt(num);
            result.X = value.X * num2;
            result.Y = value.Y * num2;
            result.Z = value.Z * num2;
        }

        // Token: 0x06003999 RID: 14745 RVA: 0x00597E9C File Offset: 0x0059609C
        public static Vector3 Cross(Vector3 vector1, Vector3 vector2)
        {
            Vector3 result;
            result.X = vector1.Y * vector2.Z - vector1.Z * vector2.Y;
            result.Y = vector1.Z * vector2.X - vector1.X * vector2.Z;
            result.Z = vector1.X * vector2.Y - vector1.Y * vector2.X;
            return result;
        }

        // Token: 0x0600399A RID: 14746 RVA: 0x00597F18 File Offset: 0x00596118
        public static void Cross(ref Vector3 vector1, ref Vector3 vector2, out Vector3 result)
        {
            float x = vector1.Y * vector2.Z - vector1.Z * vector2.Y;
            float y = vector1.Z * vector2.X - vector1.X * vector2.Z;
            float z = vector1.X * vector2.Y - vector1.Y * vector2.X;
            result.X = x;
            result.Y = y;
            result.Z = z;
        }

        // Token: 0x0600399B RID: 14747 RVA: 0x00597F90 File Offset: 0x00596190
        public static Vector3 Reflect(Vector3 vector, Vector3 normal)
        {
            float num = vector.X * normal.X + vector.Y * normal.Y + vector.Z * normal.Z;
            Vector3 result;
            result.X = vector.X - 2f * num * normal.X;
            result.Y = vector.Y - 2f * num * normal.Y;
            result.Z = vector.Z - 2f * num * normal.Z;
            return result;
        }

        // Token: 0x0600399C RID: 14748 RVA: 0x00598024 File Offset: 0x00596224
        public static void Reflect(ref Vector3 vector, ref Vector3 normal, out Vector3 result)
        {
            float num = vector.X * normal.X + vector.Y * normal.Y + vector.Z * normal.Z;
            result.X = vector.X - 2f * num * normal.X;
            result.Y = vector.Y - 2f * num * normal.Y;
            result.Z = vector.Z - 2f * num * normal.Z;
        }

        // Token: 0x0600399D RID: 14749 RVA: 0x005980B0 File Offset: 0x005962B0
        public static Vector3 Min(Vector3 value1, Vector3 value2)
        {
            Vector3 result;
            result.X = ((value1.X < value2.X) ? value1.X : value2.X);
            result.Y = ((value1.Y < value2.Y) ? value1.Y : value2.Y);
            result.Z = ((value1.Z < value2.Z) ? value1.Z : value2.Z);
            return result;
        }

        // Token: 0x0600399E RID: 14750 RVA: 0x0059812C File Offset: 0x0059632C
        public static void Min(ref Vector3 value1, ref Vector3 value2, out Vector3 result)
        {
            result.X = ((value1.X < value2.X) ? value1.X : value2.X);
            result.Y = ((value1.Y < value2.Y) ? value1.Y : value2.Y);
            result.Z = ((value1.Z < value2.Z) ? value1.Z : value2.Z);
        }

        // Token: 0x0600399F RID: 14751 RVA: 0x005981A0 File Offset: 0x005963A0
        public static Vector3 Max(Vector3 value1, Vector3 value2)
        {
            Vector3 result;
            result.X = ((value1.X > value2.X) ? value1.X : value2.X);
            result.Y = ((value1.Y > value2.Y) ? value1.Y : value2.Y);
            result.Z = ((value1.Z > value2.Z) ? value1.Z : value2.Z);
            return result;
        }

        // Token: 0x060039A0 RID: 14752 RVA: 0x0059821C File Offset: 0x0059641C
        public static void Max(ref Vector3 value1, ref Vector3 value2, out Vector3 result)
        {
            result.X = ((value1.X > value2.X) ? value1.X : value2.X);
            result.Y = ((value1.Y > value2.Y) ? value1.Y : value2.Y);
            result.Z = ((value1.Z > value2.Z) ? value1.Z : value2.Z);
        }

        // Token: 0x060039A1 RID: 14753 RVA: 0x00598290 File Offset: 0x00596490
        public static Vector3 Clamp(Vector3 value1, Vector3 min, Vector3 max)
        {
            float num = value1.X;
            num = ((num > max.X) ? max.X : num);
            num = ((num < min.X) ? min.X : num);
            float num2 = value1.Y;
            num2 = ((num2 > max.Y) ? max.Y : num2);
            num2 = ((num2 < min.Y) ? min.Y : num2);
            float num3 = value1.Z;
            num3 = ((num3 > max.Z) ? max.Z : num3);
            num3 = ((num3 < min.Z) ? min.Z : num3);
            Vector3 result;
            result.X = num;
            result.Y = num2;
            result.Z = num3;
            return result;
        }

        // Token: 0x060039A2 RID: 14754 RVA: 0x00598344 File Offset: 0x00596544
        public static void Clamp(ref Vector3 value1, ref Vector3 min, ref Vector3 max, out Vector3 result)
        {
            float num = value1.X;
            num = ((num > max.X) ? max.X : num);
            num = ((num < min.X) ? min.X : num);
            float num2 = value1.Y;
            num2 = ((num2 > max.Y) ? max.Y : num2);
            num2 = ((num2 < min.Y) ? min.Y : num2);
            float num3 = value1.Z;
            num3 = ((num3 > max.Z) ? max.Z : num3);
            num3 = ((num3 < min.Z) ? min.Z : num3);
            result.X = num;
            result.Y = num2;
            result.Z = num3;
        }

        // Token: 0x060039A3 RID: 14755 RVA: 0x005983F0 File Offset: 0x005965F0
        public static Vector3 Lerp(Vector3 value1, Vector3 value2, float amount)
        {
            Vector3 result;
            result.X = value1.X + (value2.X - value1.X) * amount;
            result.Y = value1.Y + (value2.Y - value1.Y) * amount;
            result.Z = value1.Z + (value2.Z - value1.Z) * amount;
            return result;
        }

        // Token: 0x060039A4 RID: 14756 RVA: 0x0059845C File Offset: 0x0059665C
        public static void Lerp(ref Vector3 value1, ref Vector3 value2, float amount, out Vector3 result)
        {
            result.X = value1.X + (value2.X - value1.X) * amount;
            result.Y = value1.Y + (value2.Y - value1.Y) * amount;
            result.Z = value1.Z + (value2.Z - value1.Z) * amount;
        }

        // Token: 0x060039A5 RID: 14757 RVA: 0x005984C0 File Offset: 0x005966C0
        public static Vector3 Barycentric(Vector3 value1, Vector3 value2, Vector3 value3, float amount1, float amount2)
        {
            Vector3 result;
            result.X = value1.X + amount1 * (value2.X - value1.X) + amount2 * (value3.X - value1.X);
            result.Y = value1.Y + amount1 * (value2.Y - value1.Y) + amount2 * (value3.Y - value1.Y);
            result.Z = value1.Z + amount1 * (value2.Z - value1.Z) + amount2 * (value3.Z - value1.Z);
            return result;
        }

        // Token: 0x060039A6 RID: 14758 RVA: 0x00598560 File Offset: 0x00596760
        public static void Barycentric(ref Vector3 value1, ref Vector3 value2, ref Vector3 value3, float amount1, float amount2, out Vector3 result)
        {
            result.X = value1.X + amount1 * (value2.X - value1.X) + amount2 * (value3.X - value1.X);
            result.Y = value1.Y + amount1 * (value2.Y - value1.Y) + amount2 * (value3.Y - value1.Y);
            result.Z = value1.Z + amount1 * (value2.Z - value1.Z) + amount2 * (value3.Z - value1.Z);
        }

        // Token: 0x060039A7 RID: 14759 RVA: 0x005985F8 File Offset: 0x005967F8
        public static Vector3 SmoothStep(Vector3 value1, Vector3 value2, float amount)
        {
            amount = ((amount > 1f) ? 1f : ((amount < 0f) ? 0f : amount));
            amount = amount * amount * (3f - 2f * amount);
            Vector3 result;
            result.X = value1.X + (value2.X - value1.X) * amount;
            result.Y = value1.Y + (value2.Y - value1.Y) * amount;
            result.Z = value1.Z + (value2.Z - value1.Z) * amount;
            return result;
        }

        // Token: 0x060039A8 RID: 14760 RVA: 0x00598698 File Offset: 0x00596898
        public static void SmoothStep(ref Vector3 value1, ref Vector3 value2, float amount, out Vector3 result)
        {
            amount = ((amount > 1f) ? 1f : ((amount < 0f) ? 0f : amount));
            amount = amount * amount * (3f - 2f * amount);
            result.X = value1.X + (value2.X - value1.X) * amount;
            result.Y = value1.Y + (value2.Y - value1.Y) * amount;
            result.Z = value1.Z + (value2.Z - value1.Z) * amount;
        }

        // Token: 0x060039A9 RID: 14761 RVA: 0x00598730 File Offset: 0x00596930
        public static Vector3 CatmullRom(Vector3 value1, Vector3 value2, Vector3 value3, Vector3 value4, float amount)
        {
            float num = amount * amount;
            float num2 = amount * num;
            Vector3 result;
            result.X = 0.5f * (2f * value2.X + (-value1.X + value3.X) * amount + (2f * value1.X - 5f * value2.X + 4f * value3.X - value4.X) * num + (-value1.X + 3f * value2.X - 3f * value3.X + value4.X) * num2);
            result.Y = 0.5f * (2f * value2.Y + (-value1.Y + value3.Y) * amount + (2f * value1.Y - 5f * value2.Y + 4f * value3.Y - value4.Y) * num + (-value1.Y + 3f * value2.Y - 3f * value3.Y + value4.Y) * num2);
            result.Z = 0.5f * (2f * value2.Z + (-value1.Z + value3.Z) * amount + (2f * value1.Z - 5f * value2.Z + 4f * value3.Z - value4.Z) * num + (-value1.Z + 3f * value2.Z - 3f * value3.Z + value4.Z) * num2);
            return result;
        }

        // Token: 0x060039AA RID: 14762 RVA: 0x005988E0 File Offset: 0x00596AE0
        public static void CatmullRom(ref Vector3 value1, ref Vector3 value2, ref Vector3 value3, ref Vector3 value4, float amount, out Vector3 result)
        {
            float num = amount * amount;
            float num2 = amount * num;
            result.X = 0.5f * (2f * value2.X + (-value1.X + value3.X) * amount + (2f * value1.X - 5f * value2.X + 4f * value3.X - value4.X) * num + (-value1.X + 3f * value2.X - 3f * value3.X + value4.X) * num2);
            result.Y = 0.5f * (2f * value2.Y + (-value1.Y + value3.Y) * amount + (2f * value1.Y - 5f * value2.Y + 4f * value3.Y - value4.Y) * num + (-value1.Y + 3f * value2.Y - 3f * value3.Y + value4.Y) * num2);
            result.Z = 0.5f * (2f * value2.Z + (-value1.Z + value3.Z) * amount + (2f * value1.Z - 5f * value2.Z + 4f * value3.Z - value4.Z) * num + (-value1.Z + 3f * value2.Z - 3f * value3.Z + value4.Z) * num2);
        }

        // Token: 0x060039AB RID: 14763 RVA: 0x00598A8C File Offset: 0x00596C8C
        public static Vector3 Hermite(Vector3 value1, Vector3 tangent1, Vector3 value2, Vector3 tangent2, float amount)
        {
            float num = amount * amount;
            float num2 = amount * num;
            float num3 = 2f * num2 - 3f * num + 1f;
            float num4 = -2f * num2 + 3f * num;
            float num5 = num2 - 2f * num + amount;
            float num6 = num2 - num;
            Vector3 result;
            result.X = value1.X * num3 + value2.X * num4 + tangent1.X * num5 + tangent2.X * num6;
            result.Y = value1.Y * num3 + value2.Y * num4 + tangent1.Y * num5 + tangent2.Y * num6;
            result.Z = value1.Z * num3 + value2.Z * num4 + tangent1.Z * num5 + tangent2.Z * num6;
            return result;
        }

        // Token: 0x060039AC RID: 14764 RVA: 0x00598B6C File Offset: 0x00596D6C
        public static void Hermite(ref Vector3 value1, ref Vector3 tangent1, ref Vector3 value2, ref Vector3 tangent2, float amount, out Vector3 result)
        {
            float num = amount * amount;
            float num2 = amount * num;
            float num3 = 2f * num2 - 3f * num + 1f;
            float num4 = -2f * num2 + 3f * num;
            float num5 = num2 - 2f * num + amount;
            float num6 = num2 - num;
            result.X = value1.X * num3 + value2.X * num4 + tangent1.X * num5 + tangent2.X * num6;
            result.Y = value1.Y * num3 + value2.Y * num4 + tangent1.Y * num5 + tangent2.Y * num6;
            result.Z = value1.Z * num3 + value2.Z * num4 + tangent1.Z * num5 + tangent2.Z * num6;
        }

        // Token: 0x060039AD RID: 14765 RVA: 0x00598C44 File Offset: 0x00596E44
        public static Vector3 Transform(Vector3 position, Matrix matrix)
        {
            float x = position.X * matrix.M11 + position.Y * matrix.M21 + position.Z * matrix.M31 + matrix.M41;
            float y = position.X * matrix.M12 + position.Y * matrix.M22 + position.Z * matrix.M32 + matrix.M42;
            float z = position.X * matrix.M13 + position.Y * matrix.M23 + position.Z * matrix.M33 + matrix.M43;
            Vector3 result;
            result.X = x;
            result.Y = y;
            result.Z = z;
            return result;
        }

        // Token: 0x060039AE RID: 14766 RVA: 0x00598D04 File Offset: 0x00596F04
        public static void Transform(ref Vector3 position, ref Matrix matrix, out Vector3 result)
        {
            float x = position.X * matrix.M11 + position.Y * matrix.M21 + position.Z * matrix.M31 + matrix.M41;
            float y = position.X * matrix.M12 + position.Y * matrix.M22 + position.Z * matrix.M32 + matrix.M42;
            float z = position.X * matrix.M13 + position.Y * matrix.M23 + position.Z * matrix.M33 + matrix.M43;
            result.X = x;
            result.Y = y;
            result.Z = z;
        }

        // Token: 0x060039AF RID: 14767 RVA: 0x00598DBC File Offset: 0x00596FBC
        public static Vector3 TransformNormal(Vector3 normal, Matrix matrix)
        {
            float x = normal.X * matrix.M11 + normal.Y * matrix.M21 + normal.Z * matrix.M31;
            float y = normal.X * matrix.M12 + normal.Y * matrix.M22 + normal.Z * matrix.M32;
            float z = normal.X * matrix.M13 + normal.Y * matrix.M23 + normal.Z * matrix.M33;
            Vector3 result;
            result.X = x;
            result.Y = y;
            result.Z = z;
            return result;
        }

        // Token: 0x060039B0 RID: 14768 RVA: 0x00598E68 File Offset: 0x00597068
        public static void TransformNormal(ref Vector3 normal, ref Matrix matrix, out Vector3 result)
        {
            float x = normal.X * matrix.M11 + normal.Y * matrix.M21 + normal.Z * matrix.M31;
            float y = normal.X * matrix.M12 + normal.Y * matrix.M22 + normal.Z * matrix.M32;
            float z = normal.X * matrix.M13 + normal.Y * matrix.M23 + normal.Z * matrix.M33;
            result.X = x;
            result.Y = y;
            result.Z = z;
        }

        // Token: 0x060039B1 RID: 14769 RVA: 0x00598F0C File Offset: 0x0059710C
        public static void Transform(Vector3[] sourceArray, ref Matrix matrix, Vector3[] destinationArray)
        {
            bool flag = sourceArray == null;
            if (flag)
            {
                throw new ArgumentNullException("sourceArray");
            }
            bool flag2 = destinationArray == null;
            if (flag2)
            {
                throw new ArgumentNullException("destinationArray");
            }
            bool flag3 = destinationArray.Length < sourceArray.Length;
            if (flag3)
            {
                throw new ArgumentException("NotEnoughTargetSize");
            }
            for (int i = 0; i < sourceArray.Length; i++)
            {
                float x = sourceArray[i].X;
                float y = sourceArray[i].Y;
                float z = sourceArray[i].Z;
                destinationArray[i].X = x * matrix.M11 + y * matrix.M21 + z * matrix.M31 + matrix.M41;
                destinationArray[i].Y = x * matrix.M12 + y * matrix.M22 + z * matrix.M32 + matrix.M42;
                destinationArray[i].Z = x * matrix.M13 + y * matrix.M23 + z * matrix.M33 + matrix.M43;
            }
        }

        // Token: 0x060039B2 RID: 14770 RVA: 0x00599030 File Offset: 0x00597230
        public static void Transform(Vector3[] sourceArray, int sourceIndex, ref Matrix matrix, Vector3[] destinationArray, int destinationIndex, int length)
        {
            bool flag = sourceArray == null;
            if (flag)
            {
                throw new ArgumentNullException("sourceArray");
            }
            bool flag2 = destinationArray == null;
            if (flag2)
            {
                throw new ArgumentNullException("destinationArray");
            }
            bool flag3 = sourceArray.Length < sourceIndex + (long)length;
            if (flag3)
            {
                throw new ArgumentException("NotEnoughSourceSize");
            }
            bool flag4 = destinationArray.Length < destinationIndex + (long)length;
            if (flag4)
            {
                throw new ArgumentException("NotEnoughTargetSize");
            }
            while (length > 0)
            {
                float x = sourceArray[sourceIndex].X;
                float y = sourceArray[sourceIndex].Y;
                float z = sourceArray[sourceIndex].Z;
                destinationArray[destinationIndex].X = x * matrix.M11 + y * matrix.M21 + z * matrix.M31 + matrix.M41;
                destinationArray[destinationIndex].Y = x * matrix.M12 + y * matrix.M22 + z * matrix.M32 + matrix.M42;
                destinationArray[destinationIndex].Z = x * matrix.M13 + y * matrix.M23 + z * matrix.M33 + matrix.M43;
                sourceIndex++;
                destinationIndex++;
                length--;
            }
        }

        // Token: 0x060039B3 RID: 14771 RVA: 0x00599184 File Offset: 0x00597384
        public static void TransformNormal(Vector3[] sourceArray, ref Matrix matrix, Vector3[] destinationArray)
        {
            bool flag = sourceArray == null;
            if (flag)
            {
                throw new ArgumentNullException("sourceArray");
            }
            bool flag2 = destinationArray == null;
            if (flag2)
            {
                throw new ArgumentNullException("destinationArray");
            }
            bool flag3 = destinationArray.Length < sourceArray.Length;
            if (flag3)
            {
                throw new ArgumentException("NotEnoughTargetSize");
            }
            for (int i = 0; i < sourceArray.Length; i++)
            {
                float x = sourceArray[i].X;
                float y = sourceArray[i].Y;
                float z = sourceArray[i].Z;
                destinationArray[i].X = x * matrix.M11 + y * matrix.M21 + z * matrix.M31;
                destinationArray[i].Y = x * matrix.M12 + y * matrix.M22 + z * matrix.M32;
                destinationArray[i].Z = x * matrix.M13 + y * matrix.M23 + z * matrix.M33;
            }
        }

        // Token: 0x060039B4 RID: 14772 RVA: 0x00599294 File Offset: 0x00597494
        public static void TransformNormal(Vector3[] sourceArray, int sourceIndex, ref Matrix matrix, Vector3[] destinationArray, int destinationIndex, int length)
        {
            bool flag = sourceArray == null;
            if (flag)
            {
                throw new ArgumentNullException("sourceArray");
            }
            bool flag2 = destinationArray == null;
            if (flag2)
            {
                throw new ArgumentNullException("destinationArray");
            }
            bool flag3 = sourceArray.Length < sourceIndex + (long)length;
            if (flag3)
            {
                throw new ArgumentException("NotEnoughSourceSize");
            }
            bool flag4 = destinationArray.Length < destinationIndex + (long)length;
            if (flag4)
            {
                throw new ArgumentException("NotEnoughTargetSize");
            }
            while (length > 0)
            {
                float x = sourceArray[sourceIndex].X;
                float y = sourceArray[sourceIndex].Y;
                float z = sourceArray[sourceIndex].Z;
                destinationArray[destinationIndex].X = x * matrix.M11 + y * matrix.M21 + z * matrix.M31;
                destinationArray[destinationIndex].Y = x * matrix.M12 + y * matrix.M22 + z * matrix.M32;
                destinationArray[destinationIndex].Z = x * matrix.M13 + y * matrix.M23 + z * matrix.M33;
                sourceIndex++;
                destinationIndex++;
                length--;
            }
        }

        // Token: 0x060039B5 RID: 14773 RVA: 0x005993D4 File Offset: 0x005975D4
        public static Vector3 Negate(Vector3 value)
        {
            Vector3 result;
            result.X = -value.X;
            result.Y = -value.Y;
            result.Z = -value.Z;
            return result;
        }

        // Token: 0x060039B6 RID: 14774 RVA: 0x00599414 File Offset: 0x00597614
        public static void Negate(ref Vector3 value, out Vector3 result)
        {
            result.X = -value.X;
            result.Y = -value.Y;
            result.Z = -value.Z;
        }

        // Token: 0x060039B7 RID: 14775 RVA: 0x00599440 File Offset: 0x00597640
        public static Vector3 Add(Vector3 value1, Vector3 value2)
        {
            Vector3 result;
            result.X = value1.X + value2.X;
            result.Y = value1.Y + value2.Y;
            result.Z = value1.Z + value2.Z;
            return result;
        }

        // Token: 0x060039B8 RID: 14776 RVA: 0x00599490 File Offset: 0x00597690
        public static void Add(ref Vector3 value1, ref Vector3 value2, out Vector3 result)
        {
            result.X = value1.X + value2.X;
            result.Y = value1.Y + value2.Y;
            result.Z = value1.Z + value2.Z;
        }

        // Token: 0x060039B9 RID: 14777 RVA: 0x005994CC File Offset: 0x005976CC
        public static Vector3 Subtract(Vector3 value1, Vector3 value2)
        {
            Vector3 result;
            result.X = value1.X - value2.X;
            result.Y = value1.Y - value2.Y;
            result.Z = value1.Z - value2.Z;
            return result;
        }

        // Token: 0x060039BA RID: 14778 RVA: 0x0059951C File Offset: 0x0059771C
        public static void Subtract(ref Vector3 value1, ref Vector3 value2, out Vector3 result)
        {
            result.X = value1.X - value2.X;
            result.Y = value1.Y - value2.Y;
            result.Z = value1.Z - value2.Z;
        }

        // Token: 0x060039BB RID: 14779 RVA: 0x00599558 File Offset: 0x00597758
        public static Vector3 Multiply(Vector3 value1, Vector3 value2)
        {
            Vector3 result;
            result.X = value1.X * value2.X;
            result.Y = value1.Y * value2.Y;
            result.Z = value1.Z * value2.Z;
            return result;
        }

        // Token: 0x060039BC RID: 14780 RVA: 0x005995A8 File Offset: 0x005977A8
        public static void Multiply(ref Vector3 value1, ref Vector3 value2, out Vector3 result)
        {
            result.X = value1.X * value2.X;
            result.Y = value1.Y * value2.Y;
            result.Z = value1.Z * value2.Z;
        }

        // Token: 0x060039BD RID: 14781 RVA: 0x005995E4 File Offset: 0x005977E4
        public static Vector3 Multiply(Vector3 value1, float scaleFactor)
        {
            Vector3 result;
            result.X = value1.X * scaleFactor;
            result.Y = value1.Y * scaleFactor;
            result.Z = value1.Z * scaleFactor;
            return result;
        }

        // Token: 0x060039BE RID: 14782 RVA: 0x00599624 File Offset: 0x00597824
        public static void Multiply(ref Vector3 value1, float scaleFactor, out Vector3 result)
        {
            result.X = value1.X * scaleFactor;
            result.Y = value1.Y * scaleFactor;
            result.Z = value1.Z * scaleFactor;
        }

        // Token: 0x060039BF RID: 14783 RVA: 0x00599654 File Offset: 0x00597854
        public static Vector3 Divide(Vector3 value1, Vector3 value2)
        {
            Vector3 result;
            result.X = value1.X / value2.X;
            result.Y = value1.Y / value2.Y;
            result.Z = value1.Z / value2.Z;
            return result;
        }

        // Token: 0x060039C0 RID: 14784 RVA: 0x005996A4 File Offset: 0x005978A4
        public static void Divide(ref Vector3 value1, ref Vector3 value2, out Vector3 result)
        {
            result.X = value1.X / value2.X;
            result.Y = value1.Y / value2.Y;
            result.Z = value1.Z / value2.Z;
        }

        // Token: 0x060039C1 RID: 14785 RVA: 0x005996E0 File Offset: 0x005978E0
        public static Vector3 Divide(Vector3 value1, float value2)
        {
            float num = 1f / value2;
            Vector3 result;
            result.X = value1.X * num;
            result.Y = value1.Y * num;
            result.Z = value1.Z * num;
            return result;
        }

        // Token: 0x060039C2 RID: 14786 RVA: 0x00599728 File Offset: 0x00597928
        public static void Divide(ref Vector3 value1, float value2, out Vector3 result)
        {
            float num = 1f / value2;
            result.X = value1.X * num;
            result.Y = value1.Y * num;
            result.Z = value1.Z * num;
        }

        // Token: 0x060039C3 RID: 14787 RVA: 0x00599768 File Offset: 0x00597968
        public static Vector3 operator -(Vector3 value)
        {
            Vector3 result;
            result.X = -value.X;
            result.Y = -value.Y;
            result.Z = -value.Z;
            return result;
        }

        // Token: 0x060039C4 RID: 14788 RVA: 0x005997A8 File Offset: 0x005979A8
        public static bool operator ==(Vector3 value1, Vector3 value2)
        {
            return value1.X == value2.X && value1.Y == value2.Y && value1.Z == value2.Z;
        }

        // Token: 0x060039C5 RID: 14789 RVA: 0x005997E8 File Offset: 0x005979E8
        public static bool operator !=(Vector3 value1, Vector3 value2)
        {
            return value1.X != value2.X || value1.Y != value2.Y || value1.Z != value2.Z;
        }

        // Token: 0x060039C6 RID: 14790 RVA: 0x0059982C File Offset: 0x00597A2C
        public static Vector3 operator +(Vector3 value1, Vector3 value2)
        {
            Vector3 result;
            result.X = value1.X + value2.X;
            result.Y = value1.Y + value2.Y;
            result.Z = value1.Z + value2.Z;
            return result;
        }

        // Token: 0x060039C7 RID: 14791 RVA: 0x0059987C File Offset: 0x00597A7C
        public static Vector3 operator -(Vector3 value1, Vector3 value2)
        {
            Vector3 result;
            result.X = value1.X - value2.X;
            result.Y = value1.Y - value2.Y;
            result.Z = value1.Z - value2.Z;
            return result;
        }

        // Token: 0x060039C8 RID: 14792 RVA: 0x005998CC File Offset: 0x00597ACC
        public static Vector3 operator *(Vector3 value1, Vector3 value2)
        {
            Vector3 result;
            result.X = value1.X * value2.X;
            result.Y = value1.Y * value2.Y;
            result.Z = value1.Z * value2.Z;
            return result;
        }

        // Token: 0x060039C9 RID: 14793 RVA: 0x0059991C File Offset: 0x00597B1C
        public static Vector3 operator *(Vector3 value, float scaleFactor)
        {
            Vector3 result;
            result.X = value.X * scaleFactor;
            result.Y = value.Y * scaleFactor;
            result.Z = value.Z * scaleFactor;
            return result;
        }

        // Token: 0x060039CA RID: 14794 RVA: 0x0059995C File Offset: 0x00597B5C
        public static Vector3 operator *(float scaleFactor, Vector3 value)
        {
            Vector3 result;
            result.X = value.X * scaleFactor;
            result.Y = value.Y * scaleFactor;
            result.Z = value.Z * scaleFactor;
            return result;
        }

        // Token: 0x060039CB RID: 14795 RVA: 0x0059999C File Offset: 0x00597B9C
        public static Vector3 operator /(Vector3 value1, Vector3 value2)
        {
            Vector3 result;
            result.X = value1.X / value2.X;
            result.Y = value1.Y / value2.Y;
            result.Z = value1.Z / value2.Z;
            return result;
        }

        // Token: 0x060039CC RID: 14796 RVA: 0x005999EC File Offset: 0x00597BEC
        public static Vector3 operator /(Vector3 value, float divider)
        {
            float num = 1f / divider;
            Vector3 result;
            result.X = value.X * num;
            result.Y = value.Y * num;
            result.Z = value.Z * num;
            return result;
        }

        // Token: 0x040061D0 RID: 25040
        public float X;

        // Token: 0x040061D1 RID: 25041
        public float Y;

        // Token: 0x040061D2 RID: 25042
        public float Z;

        // Token: 0x040061D3 RID: 25043
        private static Vector3 _zero = default(Vector3);

        // Token: 0x040061D4 RID: 25044
        private static Vector3 _one = new Vector3(1f, 1f, 1f);

        // Token: 0x040061D5 RID: 25045
        private static Vector3 _unitX = new Vector3(1f, 0f, 0f);

        // Token: 0x040061D6 RID: 25046
        private static Vector3 _unitY = new Vector3(0f, 1f, 0f);

        // Token: 0x040061D7 RID: 25047
        private static Vector3 _unitZ = new Vector3(0f, 0f, 1f);

        // Token: 0x040061D8 RID: 25048
        private static Vector3 _up = new Vector3(0f, 1f, 0f);

        // Token: 0x040061D9 RID: 25049
        private static Vector3 _down = new Vector3(0f, -1f, 0f);

        // Token: 0x040061DA RID: 25050
        private static Vector3 _right = new Vector3(1f, 0f, 0f);

        // Token: 0x040061DB RID: 25051
        private static Vector3 _left = new Vector3(-1f, 0f, 0f);

        // Token: 0x040061DC RID: 25052
        private static Vector3 _forward = new Vector3(0f, 0f, -1f);

        // Token: 0x040061DD RID: 25053
        private static Vector3 _backward = new Vector3(0f, 0f, 1f);
    }
}
