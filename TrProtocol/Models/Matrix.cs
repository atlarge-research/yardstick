using System;

namespace TrProtocol.Models
{
    // Token: 0x02000863 RID: 2147
    public struct Matrix
    {
        // Token: 0x17000504 RID: 1284
        // (get) Token: 0x060038CF RID: 14543 RVA: 0x00592B28 File Offset: 0x00590D28
        public static Matrix Identity => Matrix.identity;

        // Token: 0x17000505 RID: 1285
        // (get) Token: 0x060038D0 RID: 14544 RVA: 0x00592B40 File Offset: 0x00590D40
        // (set) Token: 0x060038D1 RID: 14545 RVA: 0x00592B6C File Offset: 0x00590D6C
        public Vector3 Translation
        {
            get => new Vector3(M41, M42, M43);
            set
            {
                M41 = value.X;
                M42 = value.Y;
                M43 = value.Z;
            }
        }

        // Token: 0x060038D2 RID: 14546 RVA: 0x00592B94 File Offset: 0x00590D94
        public static Matrix CreateScale(float scale)
        {
            Matrix result = Matrix.Identity;
            result.M33 = scale;
            result.M22 = scale;
            result.M11 = scale;
            return result;
        }

        // Token: 0x060038D3 RID: 14547 RVA: 0x00592BCC File Offset: 0x00590DCC
        public Matrix(float m11, float m12, float m13, float m14, float m21, float m22, float m23, float m24, float m31, float m32, float m33, float m34, float m41, float m42, float m43, float m44)
        {
            M11 = m11;
            M12 = m12;
            M13 = m13;
            M14 = m14;
            M21 = m21;
            M22 = m22;
            M23 = m23;
            M24 = m24;
            M31 = m31;
            M32 = m32;
            M33 = m33;
            M34 = m34;
            M41 = m41;
            M42 = m42;
            M43 = m43;
            M44 = m44;
        }

        // Token: 0x060038D4 RID: 14548 RVA: 0x00592C58 File Offset: 0x00590E58
        public static Matrix CreateRotationZ(float radians)
        {
            float num = (float)Math.Cos(radians);
            float num2 = (float)Math.Sin(radians);
            Matrix result;
            result.M11 = num;
            result.M12 = num2;
            result.M13 = 0f;
            result.M14 = 0f;
            result.M21 = -num2;
            result.M22 = num;
            result.M23 = 0f;
            result.M24 = 0f;
            result.M31 = 0f;
            result.M32 = 0f;
            result.M33 = 1f;
            result.M34 = 0f;
            result.M41 = 0f;
            result.M42 = 0f;
            result.M43 = 0f;
            result.M44 = 1f;
            return result;
        }

        // Token: 0x060038D5 RID: 14549 RVA: 0x00592D30 File Offset: 0x00590F30
        public static Matrix CreateScale(float xScale, float yScale, float zScale)
        {
            Matrix result;
            result.M11 = xScale;
            result.M12 = 0f;
            result.M13 = 0f;
            result.M14 = 0f;
            result.M21 = 0f;
            result.M22 = yScale;
            result.M23 = 0f;
            result.M24 = 0f;
            result.M31 = 0f;
            result.M32 = 0f;
            result.M33 = zScale;
            result.M34 = 0f;
            result.M41 = 0f;
            result.M42 = 0f;
            result.M43 = 0f;
            result.M44 = 1f;
            return result;
        }

        // Token: 0x060038D6 RID: 14550 RVA: 0x00592DF8 File Offset: 0x00590FF8
        public static Matrix operator *(Matrix matrix1, Matrix matrix2)
        {
            Matrix result;
            result.M11 = matrix1.M11 * matrix2.M11 + matrix1.M12 * matrix2.M21 + matrix1.M13 * matrix2.M31 + matrix1.M14 * matrix2.M41;
            result.M12 = matrix1.M11 * matrix2.M12 + matrix1.M12 * matrix2.M22 + matrix1.M13 * matrix2.M32 + matrix1.M14 * matrix2.M42;
            result.M13 = matrix1.M11 * matrix2.M13 + matrix1.M12 * matrix2.M23 + matrix1.M13 * matrix2.M33 + matrix1.M14 * matrix2.M43;
            result.M14 = matrix1.M11 * matrix2.M14 + matrix1.M12 * matrix2.M24 + matrix1.M13 * matrix2.M34 + matrix1.M14 * matrix2.M44;
            result.M21 = matrix1.M21 * matrix2.M11 + matrix1.M22 * matrix2.M21 + matrix1.M23 * matrix2.M31 + matrix1.M24 * matrix2.M41;
            result.M22 = matrix1.M21 * matrix2.M12 + matrix1.M22 * matrix2.M22 + matrix1.M23 * matrix2.M32 + matrix1.M24 * matrix2.M42;
            result.M23 = matrix1.M21 * matrix2.M13 + matrix1.M22 * matrix2.M23 + matrix1.M23 * matrix2.M33 + matrix1.M24 * matrix2.M43;
            result.M24 = matrix1.M21 * matrix2.M14 + matrix1.M22 * matrix2.M24 + matrix1.M23 * matrix2.M34 + matrix1.M24 * matrix2.M44;
            result.M31 = matrix1.M31 * matrix2.M11 + matrix1.M32 * matrix2.M21 + matrix1.M33 * matrix2.M31 + matrix1.M34 * matrix2.M41;
            result.M32 = matrix1.M31 * matrix2.M12 + matrix1.M32 * matrix2.M22 + matrix1.M33 * matrix2.M32 + matrix1.M34 * matrix2.M42;
            result.M33 = matrix1.M31 * matrix2.M13 + matrix1.M32 * matrix2.M23 + matrix1.M33 * matrix2.M33 + matrix1.M34 * matrix2.M43;
            result.M34 = matrix1.M31 * matrix2.M14 + matrix1.M32 * matrix2.M24 + matrix1.M33 * matrix2.M34 + matrix1.M34 * matrix2.M44;
            result.M41 = matrix1.M41 * matrix2.M11 + matrix1.M42 * matrix2.M21 + matrix1.M43 * matrix2.M31 + matrix1.M44 * matrix2.M41;
            result.M42 = matrix1.M41 * matrix2.M12 + matrix1.M42 * matrix2.M22 + matrix1.M43 * matrix2.M32 + matrix1.M44 * matrix2.M42;
            result.M43 = matrix1.M41 * matrix2.M13 + matrix1.M42 * matrix2.M23 + matrix1.M43 * matrix2.M33 + matrix1.M44 * matrix2.M43;
            result.M44 = matrix1.M41 * matrix2.M14 + matrix1.M42 * matrix2.M24 + matrix1.M43 * matrix2.M34 + matrix1.M44 * matrix2.M44;
            return result;
        }

        // Token: 0x060038D7 RID: 14551 RVA: 0x005931EC File Offset: 0x005913EC
        public static Matrix CreateTranslation(Vector3 position)
        {
            Matrix result;
            result.M11 = 1f;
            result.M12 = 0f;
            result.M13 = 0f;
            result.M14 = 0f;
            result.M21 = 0f;
            result.M22 = 1f;
            result.M23 = 0f;
            result.M24 = 0f;
            result.M31 = 0f;
            result.M32 = 0f;
            result.M33 = 1f;
            result.M34 = 0f;
            result.M41 = position.X;
            result.M42 = position.Y;
            result.M43 = position.Z;
            result.M44 = 1f;
            return result;
        }

        // Token: 0x060038D8 RID: 14552 RVA: 0x005932C4 File Offset: 0x005914C4
        public static Matrix CreateTranslation(float xPosition, float yPosition, float zPosition)
        {
            Matrix result;
            result.M11 = 1f;
            result.M12 = 0f;
            result.M13 = 0f;
            result.M14 = 0f;
            result.M21 = 0f;
            result.M22 = 1f;
            result.M23 = 0f;
            result.M24 = 0f;
            result.M31 = 0f;
            result.M32 = 0f;
            result.M33 = 1f;
            result.M34 = 0f;
            result.M41 = xPosition;
            result.M42 = yPosition;
            result.M43 = zPosition;
            result.M44 = 1f;
            return result;
        }

        // Token: 0x060038D9 RID: 14553 RVA: 0x0059338C File Offset: 0x0059158C
        public static Matrix Invert(Matrix matrix)
        {
            float m = matrix.M11;
            float m2 = matrix.M12;
            float m3 = matrix.M13;
            float m4 = matrix.M14;
            float m5 = matrix.M21;
            float m6 = matrix.M22;
            float m7 = matrix.M23;
            float m8 = matrix.M24;
            float m9 = matrix.M31;
            float m10 = matrix.M32;
            float m11 = matrix.M33;
            float m12 = matrix.M34;
            float m13 = matrix.M41;
            float m14 = matrix.M42;
            float m15 = matrix.M43;
            float m16 = matrix.M44;
            float num = m11 * m16 - m12 * m15;
            float num2 = m10 * m16 - m12 * m14;
            float num3 = m10 * m15 - m11 * m14;
            float num4 = m9 * m16 - m12 * m13;
            float num5 = m9 * m15 - m11 * m13;
            float num6 = m9 * m14 - m10 * m13;
            float num7 = m6 * num - m7 * num2 + m8 * num3;
            float num8 = -(m5 * num - m7 * num4 + m8 * num5);
            float num9 = m5 * num2 - m6 * num4 + m8 * num6;
            float num10 = -(m5 * num3 - m6 * num5 + m7 * num6);
            float num11 = 1f / (m * num7 + m2 * num8 + m3 * num9 + m4 * num10);
            Matrix result;
            result.M11 = num7 * num11;
            result.M21 = num8 * num11;
            result.M31 = num9 * num11;
            result.M41 = num10 * num11;
            result.M12 = -(m2 * num - m3 * num2 + m4 * num3) * num11;
            result.M22 = (m * num - m3 * num4 + m4 * num5) * num11;
            result.M32 = -(m * num2 - m2 * num4 + m4 * num6) * num11;
            result.M42 = (m * num3 - m2 * num5 + m3 * num6) * num11;
            float num12 = m7 * m16 - m8 * m15;
            float num13 = m6 * m16 - m8 * m14;
            float num14 = m6 * m15 - m7 * m14;
            float num15 = m5 * m16 - m8 * m13;
            float num16 = m5 * m15 - m7 * m13;
            float num17 = m5 * m14 - m6 * m13;
            result.M13 = (m2 * num12 - m3 * num13 + m4 * num14) * num11;
            result.M23 = -(m * num12 - m3 * num15 + m4 * num16) * num11;
            result.M33 = (m * num13 - m2 * num15 + m4 * num17) * num11;
            result.M43 = -(m * num14 - m2 * num16 + m3 * num17) * num11;
            float num18 = m7 * m12 - m8 * m11;
            float num19 = m6 * m12 - m8 * m10;
            float num20 = m6 * m11 - m7 * m10;
            float num21 = m5 * m12 - m8 * m9;
            float num22 = m5 * m11 - m7 * m9;
            float num23 = m5 * m10 - m6 * m9;
            result.M14 = -(m2 * num18 - m3 * num19 + m4 * num20) * num11;
            result.M24 = (m * num18 - m3 * num21 + m4 * num22) * num11;
            result.M34 = -(m * num19 - m2 * num21 + m4 * num23) * num11;
            result.M44 = (m * num20 - m2 * num22 + m3 * num23) * num11;
            return result;
        }

        // Token: 0x060038DA RID: 14554 RVA: 0x005936C8 File Offset: 0x005918C8
        public static Matrix CreateRotationX(float radians)
        {
            float num = (float)Math.Cos(radians);
            float num2 = (float)Math.Sin(radians);
            return new Matrix
            {
                M11 = 1f,
                M12 = 0f,
                M13 = 0f,
                M14 = 0f,
                M21 = 0f,
                M22 = num,
                M23 = num2,
                M24 = 0f,
                M31 = 0f,
                M32 = 0f - num2,
                M33 = num,
                M34 = 0f,
                M41 = 0f,
                M42 = 0f,
                M43 = 0f,
                M44 = 1f
            };
        }

        // Token: 0x060038DB RID: 14555 RVA: 0x005937AC File Offset: 0x005919AC
        public static void CreateRotationX(float radians, out Matrix result)
        {
            float num = (float)Math.Cos(radians);
            float num2 = (float)Math.Sin(radians);
            result.M11 = 1f;
            result.M12 = 0f;
            result.M13 = 0f;
            result.M14 = 0f;
            result.M21 = 0f;
            result.M22 = num;
            result.M23 = num2;
            result.M24 = 0f;
            result.M31 = 0f;
            result.M32 = 0f - num2;
            result.M33 = num;
            result.M34 = 0f;
            result.M41 = 0f;
            result.M42 = 0f;
            result.M43 = 0f;
            result.M44 = 1f;
        }

        // Token: 0x060038DC RID: 14556 RVA: 0x00593874 File Offset: 0x00591A74
        public static Matrix CreateRotationY(float radians)
        {
            float num = (float)Math.Cos(radians);
            float num2 = (float)Math.Sin(radians);
            return new Matrix
            {
                M11 = num,
                M12 = 0f,
                M13 = 0f - num2,
                M14 = 0f,
                M21 = 0f,
                M22 = 1f,
                M23 = 0f,
                M24 = 0f,
                M31 = num2,
                M32 = 0f,
                M33 = num,
                M34 = 0f,
                M41 = 0f,
                M42 = 0f,
                M43 = 0f,
                M44 = 1f
            };
        }

        // Token: 0x060038DD RID: 14557 RVA: 0x00593958 File Offset: 0x00591B58
        public static void CreateRotationY(float radians, out Matrix result)
        {
            float num = (float)Math.Cos(radians);
            float num2 = (float)Math.Sin(radians);
            result.M11 = num;
            result.M12 = 0f;
            result.M13 = 0f - num2;
            result.M14 = 0f;
            result.M21 = 0f;
            result.M22 = 1f;
            result.M23 = 0f;
            result.M24 = 0f;
            result.M31 = num2;
            result.M32 = 0f;
            result.M33 = num;
            result.M34 = 0f;
            result.M41 = 0f;
            result.M42 = 0f;
            result.M43 = 0f;
            result.M44 = 1f;
        }

        // Token: 0x060038DE RID: 14558 RVA: 0x00593A20 File Offset: 0x00591C20
        public static void CreateRotationZ(float radians, out Matrix result)
        {
            float num = (float)Math.Cos(radians);
            float num2 = (float)Math.Sin(radians);
            result.M11 = num;
            result.M12 = num2;
            result.M13 = 0f;
            result.M14 = 0f;
            result.M21 = 0f - num2;
            result.M22 = num;
            result.M23 = 0f;
            result.M24 = 0f;
            result.M31 = 0f;
            result.M32 = 0f;
            result.M33 = 1f;
            result.M34 = 0f;
            result.M41 = 0f;
            result.M42 = 0f;
            result.M43 = 0f;
            result.M44 = 1f;
        }

        // Token: 0x060038DF RID: 14559 RVA: 0x00593AE8 File Offset: 0x00591CE8
        public static Matrix CreateOrthographicOffCenter(float left, float right, float bottom, float top, float zNearPlane, float zFarPlane)
        {
            Matrix result = default(Matrix);
            result.M11 = 2f / (right - left);
            result.M12 = (result.M13 = (result.M14 = 0f));
            result.M22 = 2f / (top - bottom);
            result.M21 = (result.M23 = (result.M24 = 0f));
            result.M33 = 1f / (zNearPlane - zFarPlane);
            result.M31 = (result.M32 = (result.M34 = 0f));
            result.M41 = (left + right) / (left - right);
            result.M42 = (top + bottom) / (bottom - top);
            result.M43 = zNearPlane / (zNearPlane - zFarPlane);
            result.M44 = 1f;
            return result;
        }

        // Token: 0x060038E0 RID: 14560 RVA: 0x00593BCC File Offset: 0x00591DCC
        public static void CreateOrthographicOffCenter(float left, float right, float bottom, float top, float zNearPlane, float zFarPlane, out Matrix result)
        {
            result.M11 = 2f / (right - left);
            result.M12 = (result.M13 = (result.M14 = 0f));
            result.M22 = 2f / (top - bottom);
            result.M21 = (result.M23 = (result.M24 = 0f));
            result.M33 = 1f / (zNearPlane - zFarPlane);
            result.M31 = (result.M32 = (result.M34 = 0f));
            result.M41 = (left + right) / (left - right);
            result.M42 = (top + bottom) / (bottom - top);
            result.M43 = zNearPlane / (zNearPlane - zFarPlane);
            result.M44 = 1f;
        }

        // Token: 0x040061A4 RID: 24996
        public float M11;

        // Token: 0x040061A5 RID: 24997
        public float M12;

        // Token: 0x040061A6 RID: 24998
        public float M13;

        // Token: 0x040061A7 RID: 24999
        public float M14;

        // Token: 0x040061A8 RID: 25000
        public float M21;

        // Token: 0x040061A9 RID: 25001
        public float M22;

        // Token: 0x040061AA RID: 25002
        public float M23;

        // Token: 0x040061AB RID: 25003
        public float M24;

        // Token: 0x040061AC RID: 25004
        public float M31;

        // Token: 0x040061AD RID: 25005
        public float M32;

        // Token: 0x040061AE RID: 25006
        public float M33;

        // Token: 0x040061AF RID: 25007
        public float M34;

        // Token: 0x040061B0 RID: 25008
        public float M41;

        // Token: 0x040061B1 RID: 25009
        public float M42;

        // Token: 0x040061B2 RID: 25010
        public float M43;

        // Token: 0x040061B3 RID: 25011
        public float M44;

        // Token: 0x040061B4 RID: 25012
        private static Matrix identity = new Matrix(1f, 0f, 0f, 0f, 0f, 1f, 0f, 0f, 0f, 0f, 1f, 0f, 0f, 0f, 0f, 1f);
    }
}
