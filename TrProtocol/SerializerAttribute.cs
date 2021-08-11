using System;

namespace TrProtocol
{
    [AttributeUsage(AttributeTargets.Class | AttributeTargets.Struct | AttributeTargets.Enum)]
    public sealed class SerializerAttribute : Attribute
    {
        public IFieldSerializer serializer;
        public SerializerAttribute(Type type)
        {
            serializer = Activator.CreateInstance(type) as IFieldSerializer;
        }
    }
}
