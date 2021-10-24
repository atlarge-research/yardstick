using System;

namespace TrProtocol
{
    [AttributeUsage(AttributeTargets.Class | AttributeTargets.Struct | AttributeTargets.Enum)]
    public sealed class SerializerAttribute : Attribute
    {
        public string version;
        public IFieldSerializer serializer;

        public SerializerAttribute(Type type, string version = null)
        {
            this.version = version;
            serializer = Activator.CreateInstance(type) as IFieldSerializer;
        }
    }
}
