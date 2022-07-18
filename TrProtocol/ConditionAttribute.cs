namespace TrProtocol;

public class OutOfBoundsException : Exception
{
	public OutOfBoundsException(string message) : base(message)
	{

	}
}

[AttributeUsage(AttributeTargets.Property, AllowMultiple = false)]
public sealed class BoundsAttribute : Attribute
{
	public int UpperBound { get; set; }
	public int LowerBound { get; set; }
	public string Version { get; set; }
	public bool Interrupt { get; set; }

	public BoundsAttribute(string version, int upperBound, int lowerBound = int.MinValue, bool interrupt = true)
	{
		UpperBound = upperBound;
		LowerBound = lowerBound;
		Version = version;
		Interrupt = interrupt;
	}
}

[AttributeUsage(AttributeTargets.Property)]
public sealed class ForceSerializeAttribute : Attribute
{

}

[AttributeUsage(AttributeTargets.Property)]
public sealed class ProtocolVersionAttribute : Attribute
{
	public string Version { get; set; }

	public ProtocolVersionAttribute(string version)
	{
		Version = version;
	}
}

[AttributeUsage(AttributeTargets.Class | AttributeTargets.Property, AllowMultiple = false)]
public sealed class S2COnlyAttribute : Attribute
{

}

[AttributeUsage(AttributeTargets.Class | AttributeTargets.Property, AllowMultiple = false)]
public sealed class C2SOnlyAttribute : Attribute
{

}


[AttributeUsage(AttributeTargets.Property, AllowMultiple = false)]
public sealed class ArraySizeAttribute : Attribute
{
	public int Size { get; set; }

	public ArraySizeAttribute(int size)
	{
		Size = size;
	}
}
[AttributeUsage(AttributeTargets.Property)]
public sealed class ConditionAttribute : Attribute
{
	public string FieldName { get; set; }
	public sbyte BitIndex { get; set; }
	public bool Prediction { get; set; }

	public ConditionAttribute(string field, sbyte bit = -1, bool pred = true)
	{
		BitIndex = bit;
		FieldName = field;
		Prediction = pred;
	}
}

[AttributeUsage(AttributeTargets.Property)]
public sealed class IgnoreAttribute : Attribute
{
}
