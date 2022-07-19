using System.Reflection;

namespace TrProtocol;

public abstract class NumericFieldSerializer<T> : FieldSerializer<T>, IConfigurable
{
    private int upper, lower;
    private T zero;
    private bool interrupt, enabled;
    public override void Write(BinaryWriter bw, object o)
    {
        if (enabled)
        {
            var o2 = Convert.ToInt32(o);
            if (o2 > upper || o2 < lower)
            {
                if (interrupt)
                    throw new OutOfBoundsException(
                        $"Packet ignored due to field {typeof(T)} = {o2} out of bounds ({lower}, {upper})");
                o = zero;
            }
        }
        WriteOverride(bw, (T)o);
    }

    public IConfigurable Configure(PropertyInfo prop, string version)
    {
        foreach (var bounds in prop.GetCustomAttributes<BoundsAttribute>())
        {
            if (bounds.Version != version)
                continue;
            zero = (T)Convert.ChangeType(0, prop.PropertyType);
            upper = bounds.UpperBound;
            lower = bounds.LowerBound;
            interrupt = bounds.Interrupt;
            enabled = true;
        }
        return this;
    }
}
public abstract class FieldSerializer<T> : IFieldSerializer
{
    protected abstract T ReadOverride(BinaryReader br);

    protected abstract void WriteOverride(BinaryWriter bw, T t);

    public virtual object Read(BinaryReader br) => ReadOverride(br);

    public virtual void Write(BinaryWriter bw, object o) => WriteOverride(bw, (T)o);
}
