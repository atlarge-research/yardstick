using System;
using System.Globalization;

namespace TrProtocol.Models
{
    // Token: 0x02000869 RID: 2153
    public partial struct Vector2
    {
        // Token: 0x1700050F RID: 1295
        // (get) Token: 0x0600393A RID: 14650 RVA: 0x005965C0 File Offset: 0x005947C0
        public static Vector2 Zero => Vector2._zero;

        // Token: 0x17000510 RID: 1296
        // (get) Token: 0x0600393B RID: 14651 RVA: 0x005965D8 File Offset: 0x005947D8
        public static Vector2 One => Vector2._one;

        // Token: 0x17000511 RID: 1297
        // (get) Token: 0x0600393C RID: 14652 RVA: 0x005965F0 File Offset: 0x005947F0
        public static Vector2 UnitX => Vector2._unitX;

        // Token: 0x17000512 RID: 1298
        // (get) Token: 0x0600393D RID: 14653 RVA: 0x00596608 File Offset: 0x00594808
        public static Vector2 UnitY => Vector2._unitY;

        // Token: 0x0600393E RID: 14654 RVA: 0x00596620 File Offset: 0x00594820
        public Vector2(float x, float y)
        {
            X = x;
            Y = y;
        }

        // Token: 0x0600393F RID: 14655 RVA: 0x00596634 File Offset: 0x00594834
        public Vector2(float value)
        {
            Y = value;
            X = value;
        }

        // Token: 0x06003940 RID: 14656 RVA: 0x00596648 File Offset: 0x00594848
        public override string ToString()
        {
            CultureInfo currentCulture = CultureInfo.CurrentCulture;
            return string.Format(currentCulture, "{{X:{0} Y:{1}}}", new object[]
            {
                X.ToString(currentCulture),
                Y.ToString(currentCulture)
            });
        }

        // Token: 0x06003941 RID: 14657 RVA: 0x00596690 File Offset: 0x00594890
        public bool Equals(Vector2 other)
        {
            return X == other.X && Y == other.Y;
        }

        // Token: 0x06003942 RID: 14658 RVA: 0x005966C4 File Offset: 0x005948C4
        public override bool Equals(object obj)
        {
            bool result = false;
            bool flag = obj is Vector2;
            if (flag)
            {
                result = Equals((Vector2)obj);
            }
            return result;
        }

        // Token: 0x06003943 RID: 14659 RVA: 0x005966F8 File Offset: 0x005948F8
        public override int GetHashCode()
        {
            return X.GetHashCode() + Y.GetHashCode();
        }

        // Token: 0x06003944 RID: 14660 RVA: 0x00596724 File Offset: 0x00594924
        public float Length()
        {
            float num = X * X + Y * Y;
            return (float)Math.Sqrt(num);
        }

        // Token: 0x06003945 RID: 14661 RVA: 0x0059675C File Offset: 0x0059495C
        public float LengthSquared()
        {
            return X * X + Y * Y;
        }

        // Token: 0x06003946 RID: 14662 RVA: 0x0059678C File Offset: 0x0059498C
        public static float Distance(Vector2 value1, Vector2 value2)
        {
            float num = value1.X - value2.X;
            float num2 = value1.Y - value2.Y;
            float num3 = num * num + num2 * num2;
            return (float)Math.Sqrt(num3);
        }

        // Token: 0x06003947 RID: 14663 RVA: 0x005967CC File Offset: 0x005949CC
        public static void Distance(ref Vector2 value1, ref Vector2 value2, out float result)
        {
            float num = value1.X - value2.X;
            float num2 = value1.Y - value2.Y;
            float num3 = num * num + num2 * num2;
            result = (float)Math.Sqrt(num3);
        }

        // Token: 0x06003948 RID: 14664 RVA: 0x00596808 File Offset: 0x00594A08
        public static float DistanceSquared(Vector2 value1, Vector2 value2)
        {
            float num = value1.X - value2.X;
            float num2 = value1.Y - value2.Y;
            return num * num + num2 * num2;
        }

        // Token: 0x06003949 RID: 14665 RVA: 0x00596840 File Offset: 0x00594A40
        public static void DistanceSquared(ref Vector2 value1, ref Vector2 value2, out float result)
        {
            float num = value1.X - value2.X;
            float num2 = value1.Y - value2.Y;
            result = num * num + num2 * num2;
        }

        // Token: 0x0600394A RID: 14666 RVA: 0x00596874 File Offset: 0x00594A74
        public static float Dot(Vector2 value1, Vector2 value2)
        {
            return value1.X * value2.X + value1.Y * value2.Y;
        }

        // Token: 0x0600394B RID: 14667 RVA: 0x005968A4 File Offset: 0x00594AA4
        public static void Dot(ref Vector2 value1, ref Vector2 value2, out float result)
        {
            result = value1.X * value2.X + value1.Y * value2.Y;
        }

        // Token: 0x0600394C RID: 14668 RVA: 0x005968C4 File Offset: 0x00594AC4
        public void Normalize()
        {
            float num = X * X + Y * Y;
            float num2 = 1f / (float)Math.Sqrt(num);
            X *= num2;
            Y *= num2;
        }

        // Token: 0x0600394D RID: 14669 RVA: 0x0059691C File Offset: 0x00594B1C
        public static Vector2 Normalize(Vector2 value)
        {
            float num = value.X * value.X + value.Y * value.Y;
            float num2 = 1f / (float)Math.Sqrt(num);
            Vector2 result;
            result.X = value.X * num2;
            result.Y = value.Y * num2;
            return result;
        }

        // Token: 0x0600394E RID: 14670 RVA: 0x00596978 File Offset: 0x00594B78
        public static void Normalize(ref Vector2 value, out Vector2 result)
        {
            float num = value.X * value.X + value.Y * value.Y;
            float num2 = 1f / (float)Math.Sqrt(num);
            result.X = value.X * num2;
            result.Y = value.Y * num2;
        }

        // Token: 0x0600394F RID: 14671 RVA: 0x005969D0 File Offset: 0x00594BD0
        public static Vector2 Reflect(Vector2 vector, Vector2 normal)
        {
            float num = vector.X * normal.X + vector.Y * normal.Y;
            Vector2 result;
            result.X = vector.X - 2f * num * normal.X;
            result.Y = vector.Y - 2f * num * normal.Y;
            return result;
        }

        // Token: 0x06003950 RID: 14672 RVA: 0x00596A38 File Offset: 0x00594C38
        public static void Reflect(ref Vector2 vector, ref Vector2 normal, out Vector2 result)
        {
            float num = vector.X * normal.X + vector.Y * normal.Y;
            result.X = vector.X - 2f * num * normal.X;
            result.Y = vector.Y - 2f * num * normal.Y;
        }

        // Token: 0x06003951 RID: 14673 RVA: 0x00596A98 File Offset: 0x00594C98
        public static Vector2 Min(Vector2 value1, Vector2 value2)
        {
            Vector2 result;
            result.X = ((value1.X < value2.X) ? value1.X : value2.X);
            result.Y = ((value1.Y < value2.Y) ? value1.Y : value2.Y);
            return result;
        }

        // Token: 0x06003952 RID: 14674 RVA: 0x00596AF4 File Offset: 0x00594CF4
        public static void Min(ref Vector2 value1, ref Vector2 value2, out Vector2 result)
        {
            result.X = ((value1.X < value2.X) ? value1.X : value2.X);
            result.Y = ((value1.Y < value2.Y) ? value1.Y : value2.Y);
        }

        // Token: 0x06003953 RID: 14675 RVA: 0x00596B48 File Offset: 0x00594D48
        public static Vector2 Max(Vector2 value1, Vector2 value2)
        {
            Vector2 result;
            result.X = ((value1.X > value2.X) ? value1.X : value2.X);
            result.Y = ((value1.Y > value2.Y) ? value1.Y : value2.Y);
            return result;
        }

        // Token: 0x06003954 RID: 14676 RVA: 0x00596BA4 File Offset: 0x00594DA4
        public static void Max(ref Vector2 value1, ref Vector2 value2, out Vector2 result)
        {
            result.X = ((value1.X > value2.X) ? value1.X : value2.X);
            result.Y = ((value1.Y > value2.Y) ? value1.Y : value2.Y);
        }

        // Token: 0x06003955 RID: 14677 RVA: 0x00596BF8 File Offset: 0x00594DF8
        public static Vector2 Clamp(Vector2 value1, Vector2 min, Vector2 max)
        {
            float num = value1.X;
            num = ((num > max.X) ? max.X : num);
            num = ((num < min.X) ? min.X : num);
            float num2 = value1.Y;
            num2 = ((num2 > max.Y) ? max.Y : num2);
            num2 = ((num2 < min.Y) ? min.Y : num2);
            Vector2 result;
            result.X = num;
            result.Y = num2;
            return result;
        }

        // Token: 0x06003956 RID: 14678 RVA: 0x00596C78 File Offset: 0x00594E78
        public static void Clamp(ref Vector2 value1, ref Vector2 min, ref Vector2 max, out Vector2 result)
        {
            float num = value1.X;
            num = ((num > max.X) ? max.X : num);
            num = ((num < min.X) ? min.X : num);
            float num2 = value1.Y;
            num2 = ((num2 > max.Y) ? max.Y : num2);
            num2 = ((num2 < min.Y) ? min.Y : num2);
            result.X = num;
            result.Y = num2;
        }

        // Token: 0x06003957 RID: 14679 RVA: 0x00596CF0 File Offset: 0x00594EF0
        public static Vector2 Lerp(Vector2 value1, Vector2 value2, float amount)
        {
            Vector2 result;
            result.X = value1.X + (value2.X - value1.X) * amount;
            result.Y = value1.Y + (value2.Y - value1.Y) * amount;
            return result;
        }

        // Token: 0x06003958 RID: 14680 RVA: 0x00596D40 File Offset: 0x00594F40
        public static void Lerp(ref Vector2 value1, ref Vector2 value2, float amount, out Vector2 result)
        {
            result.X = value1.X + (value2.X - value1.X) * amount;
            result.Y = value1.Y + (value2.Y - value1.Y) * amount;
        }

        // Token: 0x06003959 RID: 14681 RVA: 0x00596D7C File Offset: 0x00594F7C
        public static Vector2 Barycentric(Vector2 value1, Vector2 value2, Vector2 value3, float amount1, float amount2)
        {
            Vector2 result;
            result.X = value1.X + amount1 * (value2.X - value1.X) + amount2 * (value3.X - value1.X);
            result.Y = value1.Y + amount1 * (value2.Y - value1.Y) + amount2 * (value3.Y - value1.Y);
            return result;
        }

        // Token: 0x0600395A RID: 14682 RVA: 0x00596DEC File Offset: 0x00594FEC
        public static void Barycentric(ref Vector2 value1, ref Vector2 value2, ref Vector2 value3, float amount1, float amount2, out Vector2 result)
        {
            result.X = value1.X + amount1 * (value2.X - value1.X) + amount2 * (value3.X - value1.X);
            result.Y = value1.Y + amount1 * (value2.Y - value1.Y) + amount2 * (value3.Y - value1.Y);
        }

        // Token: 0x0600395B RID: 14683 RVA: 0x00596E58 File Offset: 0x00595058
        public static Vector2 SmoothStep(Vector2 value1, Vector2 value2, float amount)
        {
            amount = ((amount > 1f) ? 1f : ((amount < 0f) ? 0f : amount));
            amount = amount * amount * (3f - 2f * amount);
            Vector2 result;
            result.X = value1.X + (value2.X - value1.X) * amount;
            result.Y = value1.Y + (value2.Y - value1.Y) * amount;
            return result;
        }

        // Token: 0x0600395C RID: 14684 RVA: 0x00596EDC File Offset: 0x005950DC
        public static void SmoothStep(ref Vector2 value1, ref Vector2 value2, float amount, out Vector2 result)
        {
            amount = ((amount > 1f) ? 1f : ((amount < 0f) ? 0f : amount));
            amount = amount * amount * (3f - 2f * amount);
            result.X = value1.X + (value2.X - value1.X) * amount;
            result.Y = value1.Y + (value2.Y - value1.Y) * amount;
        }

        // Token: 0x0600395D RID: 14685 RVA: 0x00596F58 File Offset: 0x00595158
        public static Vector2 CatmullRom(Vector2 value1, Vector2 value2, Vector2 value3, Vector2 value4, float amount)
        {
            float num = amount * amount;
            float num2 = amount * num;
            Vector2 result;
            result.X = 0.5f * (2f * value2.X + (-value1.X + value3.X) * amount + (2f * value1.X - 5f * value2.X + 4f * value3.X - value4.X) * num + (-value1.X + 3f * value2.X - 3f * value3.X + value4.X) * num2);
            result.Y = 0.5f * (2f * value2.Y + (-value1.Y + value3.Y) * amount + (2f * value1.Y - 5f * value2.Y + 4f * value3.Y - value4.Y) * num + (-value1.Y + 3f * value2.Y - 3f * value3.Y + value4.Y) * num2);
            return result;
        }

        // Token: 0x0600395E RID: 14686 RVA: 0x00597084 File Offset: 0x00595284
        public static void CatmullRom(ref Vector2 value1, ref Vector2 value2, ref Vector2 value3, ref Vector2 value4, float amount, out Vector2 result)
        {
            float num = amount * amount;
            float num2 = amount * num;
            result.X = 0.5f * (2f * value2.X + (-value1.X + value3.X) * amount + (2f * value1.X - 5f * value2.X + 4f * value3.X - value4.X) * num + (-value1.X + 3f * value2.X - 3f * value3.X + value4.X) * num2);
            result.Y = 0.5f * (2f * value2.Y + (-value1.Y + value3.Y) * amount + (2f * value1.Y - 5f * value2.Y + 4f * value3.Y - value4.Y) * num + (-value1.Y + 3f * value2.Y - 3f * value3.Y + value4.Y) * num2);
        }

        // Token: 0x0600395F RID: 14687 RVA: 0x005971AC File Offset: 0x005953AC
        public static Vector2 Hermite(Vector2 value1, Vector2 tangent1, Vector2 value2, Vector2 tangent2, float amount)
        {
            float num = amount * amount;
            float num2 = amount * num;
            float num3 = 2f * num2 - 3f * num + 1f;
            float num4 = -2f * num2 + 3f * num;
            float num5 = num2 - 2f * num + amount;
            float num6 = num2 - num;
            Vector2 result;
            result.X = value1.X * num3 + value2.X * num4 + tangent1.X * num5 + tangent2.X * num6;
            result.Y = value1.Y * num3 + value2.Y * num4 + tangent1.Y * num5 + tangent2.Y * num6;
            return result;
        }

        // Token: 0x06003960 RID: 14688 RVA: 0x00597260 File Offset: 0x00595460
        public static void Hermite(ref Vector2 value1, ref Vector2 tangent1, ref Vector2 value2, ref Vector2 tangent2, float amount, out Vector2 result)
        {
            float num = amount * amount;
            float num2 = amount * num;
            float num3 = 2f * num2 - 3f * num + 1f;
            float num4 = -2f * num2 + 3f * num;
            float num5 = num2 - 2f * num + amount;
            float num6 = num2 - num;
            result.X = value1.X * num3 + value2.X * num4 + tangent1.X * num5 + tangent2.X * num6;
            result.Y = value1.Y * num3 + value2.Y * num4 + tangent1.Y * num5 + tangent2.Y * num6;
        }

        // Token: 0x06003961 RID: 14689 RVA: 0x0059730C File Offset: 0x0059550C
        public static Vector2 Transform(Vector2 position, Matrix matrix)
        {
            return position;
        }

        // Token: 0x06003962 RID: 14690 RVA: 0x00597320 File Offset: 0x00595520
        public static Vector2 Negate(Vector2 value)
        {
            Vector2 result;
            result.X = -value.X;
            result.Y = -value.Y;
            return result;
        }

        // Token: 0x06003963 RID: 14691 RVA: 0x00597350 File Offset: 0x00595550
        public static void Negate(ref Vector2 value, out Vector2 result)
        {
            result.X = -value.X;
            result.Y = -value.Y;
        }

        // Token: 0x06003964 RID: 14692 RVA: 0x00597370 File Offset: 0x00595570
        public static Vector2 Add(Vector2 value1, Vector2 value2)
        {
            Vector2 result;
            result.X = value1.X + value2.X;
            result.Y = value1.Y + value2.Y;
            return result;
        }

        // Token: 0x06003965 RID: 14693 RVA: 0x005973AC File Offset: 0x005955AC
        public static void Add(ref Vector2 value1, ref Vector2 value2, out Vector2 result)
        {
            result.X = value1.X + value2.X;
            result.Y = value1.Y + value2.Y;
        }

        // Token: 0x06003966 RID: 14694 RVA: 0x005973D8 File Offset: 0x005955D8
        public static Vector2 Subtract(Vector2 value1, Vector2 value2)
        {
            Vector2 result;
            result.X = value1.X - value2.X;
            result.Y = value1.Y - value2.Y;
            return result;
        }

        // Token: 0x06003967 RID: 14695 RVA: 0x00597414 File Offset: 0x00595614
        public static void Subtract(ref Vector2 value1, ref Vector2 value2, out Vector2 result)
        {
            result.X = value1.X - value2.X;
            result.Y = value1.Y - value2.Y;
        }

        // Token: 0x06003968 RID: 14696 RVA: 0x00597440 File Offset: 0x00595640
        public static Vector2 Multiply(Vector2 value1, Vector2 value2)
        {
            Vector2 result;
            result.X = value1.X * value2.X;
            result.Y = value1.Y * value2.Y;
            return result;
        }

        // Token: 0x06003969 RID: 14697 RVA: 0x0059747C File Offset: 0x0059567C
        public static void Multiply(ref Vector2 value1, ref Vector2 value2, out Vector2 result)
        {
            result.X = value1.X * value2.X;
            result.Y = value1.Y * value2.Y;
        }

        // Token: 0x0600396A RID: 14698 RVA: 0x005974A8 File Offset: 0x005956A8
        public static Vector2 Multiply(Vector2 value1, float scaleFactor)
        {
            Vector2 result;
            result.X = value1.X * scaleFactor;
            result.Y = value1.Y * scaleFactor;
            return result;
        }

        // Token: 0x0600396B RID: 14699 RVA: 0x005974DC File Offset: 0x005956DC
        public static void Multiply(ref Vector2 value1, float scaleFactor, out Vector2 result)
        {
            result.X = value1.X * scaleFactor;
            result.Y = value1.Y * scaleFactor;
        }

        // Token: 0x0600396C RID: 14700 RVA: 0x005974FC File Offset: 0x005956FC
        public static Vector2 Divide(Vector2 value1, Vector2 value2)
        {
            Vector2 result;
            result.X = value1.X / value2.X;
            result.Y = value1.Y / value2.Y;
            return result;
        }

        // Token: 0x0600396D RID: 14701 RVA: 0x00597538 File Offset: 0x00595738
        public static void Divide(ref Vector2 value1, ref Vector2 value2, out Vector2 result)
        {
            result.X = value1.X / value2.X;
            result.Y = value1.Y / value2.Y;
        }

        // Token: 0x0600396E RID: 14702 RVA: 0x00597564 File Offset: 0x00595764
        public static Vector2 Divide(Vector2 value1, float divider)
        {
            float num = 1f / divider;
            Vector2 result;
            result.X = value1.X * num;
            result.Y = value1.Y * num;
            return result;
        }

        // Token: 0x0600396F RID: 14703 RVA: 0x005975A0 File Offset: 0x005957A0
        public static void Divide(ref Vector2 value1, float divider, out Vector2 result)
        {
            float num = 1f / divider;
            result.X = value1.X * num;
            result.Y = value1.Y * num;
        }

        // Token: 0x06003970 RID: 14704 RVA: 0x005975D4 File Offset: 0x005957D4
        public static Vector2 operator -(Vector2 value)
        {
            Vector2 result;
            result.X = -value.X;
            result.Y = -value.Y;
            return result;
        }

        // Token: 0x06003971 RID: 14705 RVA: 0x00597604 File Offset: 0x00595804
        public static bool operator ==(Vector2 value1, Vector2 value2)
        {
            return value1.X == value2.X && value1.Y == value2.Y;
        }

        // Token: 0x06003972 RID: 14706 RVA: 0x00597638 File Offset: 0x00595838
        public static bool operator !=(Vector2 value1, Vector2 value2)
        {
            return value1.X != value2.X || value1.Y != value2.Y;
        }

        // Token: 0x06003973 RID: 14707 RVA: 0x0059766C File Offset: 0x0059586C
        public static Vector2 operator +(Vector2 value1, Vector2 value2)
        {
            Vector2 result;
            result.X = value1.X + value2.X;
            result.Y = value1.Y + value2.Y;
            return result;
        }

        // Token: 0x06003974 RID: 14708 RVA: 0x005976A8 File Offset: 0x005958A8
        public static Vector2 operator -(Vector2 value1, Vector2 value2)
        {
            Vector2 result;
            result.X = value1.X - value2.X;
            result.Y = value1.Y - value2.Y;
            return result;
        }

        // Token: 0x06003975 RID: 14709 RVA: 0x005976E4 File Offset: 0x005958E4
        public static Vector2 operator *(Vector2 value1, Vector2 value2)
        {
            Vector2 result;
            result.X = value1.X * value2.X;
            result.Y = value1.Y * value2.Y;
            return result;
        }

        // Token: 0x06003976 RID: 14710 RVA: 0x00597720 File Offset: 0x00595920
        public static Vector2 operator *(Vector2 value, float scaleFactor)
        {
            Vector2 result;
            result.X = value.X * scaleFactor;
            result.Y = value.Y * scaleFactor;
            return result;
        }

        // Token: 0x06003977 RID: 14711 RVA: 0x00597754 File Offset: 0x00595954
        public static Vector2 operator *(float scaleFactor, Vector2 value)
        {
            Vector2 result;
            result.X = value.X * scaleFactor;
            result.Y = value.Y * scaleFactor;
            return result;
        }

        // Token: 0x06003978 RID: 14712 RVA: 0x00597788 File Offset: 0x00595988
        public static Vector2 operator /(Vector2 value1, Vector2 value2)
        {
            Vector2 result;
            result.X = value1.X / value2.X;
            result.Y = value1.Y / value2.Y;
            return result;
        }

        // Token: 0x06003979 RID: 14713 RVA: 0x005977C4 File Offset: 0x005959C4
        public static Vector2 operator /(Vector2 value1, float divider)
        {
            float num = 1f / divider;
            Vector2 result;
            result.X = value1.X * num;
            result.Y = value1.Y * num;
            return result;
        }

        // Token: 0x0600397A RID: 14714 RVA: 0x00597800 File Offset: 0x00595A00
        public static void Transform(ref Vector2 position, ref Matrix matrix, out Vector2 result)
        {
            float x = position.X * matrix.M11 + position.Y * matrix.M21 + matrix.M41;
            float y = position.X * matrix.M12 + position.Y * matrix.M22 + matrix.M42;
            result.X = x;
            result.Y = y;
        }

        // Token: 0x040061C9 RID: 25033
        public static Vector2[] Array;

        // Token: 0x040061CA RID: 25034
        public float X;

        // Token: 0x040061CB RID: 25035
        public float Y;

        // Token: 0x040061CC RID: 25036
        private static Vector2 _zero = default(Vector2);

        // Token: 0x040061CD RID: 25037
        private static Vector2 _one = new Vector2(1f, 1f);

        // Token: 0x040061CE RID: 25038
        private static Vector2 _unitX = new Vector2(1f, 0f);

        // Token: 0x040061CF RID: 25039
        private static Vector2 _unitY = new Vector2(0f, 1f);
    }
}
