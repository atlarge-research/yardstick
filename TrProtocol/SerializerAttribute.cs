namespace TrProtocol;

[AttributeUsage(AttributeTargets.Class | AttributeTargets.Struct | AttributeTargets.Enum, AllowMultiple = true)]
public sealed class SerializerAttribute : Attribute
{
    public string Version { get; set; }
    public IFieldSerializer Serializer { get; set; }

    public SerializerAttribute(Type type, string version = null)
    {
        Version = version;
        Serializer = Activator.CreateInstance(type) as IFieldSerializer;
    }
}
