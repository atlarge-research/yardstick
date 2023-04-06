using System.Reflection;
using System.Runtime.ConstrainedExecution;

namespace TrProtocol;

public partial class PacketSerializer
{
    static PacketSerializer()
    {
        // put all predefined serializers here
        RegisterSerializer(new GuidSerializer());
        RegisterSerializer(new StringSerializer());
        RegisterSerializer(new ByteArraySerializer());
    }

    private static readonly Dictionary<Type, IFieldSerializer> fieldSerializers = new();

    private static IFieldSerializer RequestFieldSerializer(Type t, string version = null)
    {
        foreach (var attr in t.GetCustomAttributes<SerializerAttribute>()) // try to resolve serializer according to attributes
        {
            if ((attr.Version ?? version) == version)
            {
                return attr.Serializer;
            }
        }

        if (fieldSerializers.TryGetValue(t, out IFieldSerializer value))
            return value;
        if (t.IsPrimitive || t.IsEnum)
            return fieldSerializers[t] = Activator.CreateInstance(typeof(PrimitiveFieldSerializer<>).MakeGenericType(t)) as IFieldSerializer;
        else if (t.IsArray)
            return fieldSerializers[t] = Activator.CreateInstance(typeof(ArraySerializer<>).MakeGenericType(t.GetElementType())) as IFieldSerializer;
        else
            throw new Exception($"No valid field serializer for type: {t.FullName} can be found or generated");
    }
    private static void RegisterSerializer<T>(FieldSerializer<T> serializer)
    {
        fieldSerializers[typeof(T)] = serializer;
    }

    private class GuidSerializer : FieldSerializer<Guid>
    {
        protected override Guid ReadOverride(BinaryReader br) => new(br.ReadBytes(16));
        protected override void WriteOverride(BinaryWriter bw, Guid t) => bw.Write(t.ToByteArray());
    }
    private class StringSerializer : FieldSerializer<string>
    {
        protected override string ReadOverride(BinaryReader br) => br.ReadString();
        protected override void WriteOverride(BinaryWriter bw, string t) => bw.Write(t);
    }

    private class ByteArraySerializer : FieldSerializer<byte[]>
    {
        protected override byte[] ReadOverride(BinaryReader br) => br.ReadBytes((int)(br.BaseStream.Length - br.BaseStream.Position));

        protected override void WriteOverride(BinaryWriter bw, byte[] t) => bw.Write(t);
    }

    private class ArraySerializer<T> : FieldSerializer<T[]>, IConfigurable
    {
        private int size;
        private IFieldSerializer elementSerializer;
        public ArraySerializer() : this(0)
        {

        }

        private ArraySerializer(int size)
        {
            this.size = size;
            elementSerializer = RequestFieldSerializer(typeof(T));
        }

        protected override T[] ReadOverride(BinaryReader br)
        {
            var t = new T[size];
            for (var i = 0; i < size; ++i)
                t[i] = (T)elementSerializer.Read(br);
            return t;
        }

        protected override void WriteOverride(BinaryWriter bw, T[] t)
        {
            foreach (var x in t)
                elementSerializer.Write(bw, x);
        }

        public IConfigurable Configure(PropertyInfo prop, string version)
        {
            if (elementSerializer is IConfigurable conf)
                conf.Configure(prop, version);
            return new ArraySerializer<T>()
            {
                size = prop.GetCustomAttribute<ArraySizeAttribute>().Size,
                elementSerializer = elementSerializer
            };
        }
    }
}