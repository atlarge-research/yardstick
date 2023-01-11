namespace TrProtocol.Models;

public unsafe class PrimitiveFieldSerializer<TPrimitive> : FieldSerializer<TPrimitive>
    where TPrimitive : unmanaged
{
    private static readonly int SizeOfTPrimitive = sizeof(TPrimitive);
    protected override TPrimitive ReadOverride(BinaryReader br)
    {
        Span<byte> buffer = stackalloc byte[SizeOfTPrimitive];
        br.Read(buffer);
        fixed (byte* ptr = buffer)
            return *(TPrimitive*)ptr;
    }

    protected override void WriteOverride(BinaryWriter bw, TPrimitive t)
    {
        Span<byte> buffer = stackalloc byte[SizeOfTPrimitive];
        fixed (byte* ptr = buffer)
            *(TPrimitive*)ptr = t;
        bw.Write(buffer);
    }
}
