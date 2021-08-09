namespace TrProtocol.Models
{
    // Token: 0x02000860 RID: 2144
    public interface IPackedVector
    {
        // Token: 0x060038BF RID: 14527
        Vector4 ToVector4();

        // Token: 0x060038C0 RID: 14528
        void PackFromVector4(Vector4 vector);
    }
    // Token: 0x02000861 RID: 2145
    public interface IPackedVector<TPacked> : IPackedVector
    {
        // Token: 0x17000503 RID: 1283
        // (get) Token: 0x060038C1 RID: 14529
        // (set) Token: 0x060038C2 RID: 14530
        TPacked PackedValue { get; set; }
    }
}
