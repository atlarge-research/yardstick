using System.Reflection;

namespace TrProtocol;

public partial class PacketSerializer
{
    private delegate void Serializer(object o, BinaryWriter bw);
    private delegate void Deserializer(object o, BinaryReader br);
    private delegate bool ConditionBoolEvaluater(object o);
    private delegate BitsByte ConditionBitsByteEvaluater(object o);

    private readonly Dictionary<Type, Action<BinaryWriter, Packet>> serializers = new();

    private readonly Dictionary<MessageID, Func<BinaryReader, Packet>> deserializers = new();
    private readonly Dictionary<NetModuleType, Func<BinaryReader, NetModulesPacket>> moduledeserializers = new();


    private void LoadPackets()
    {
        foreach (var type in Assembly.GetExecutingAssembly().GetTypes())
        {
            RegisterPacket(type);
        }
    }

    public void RegisterPacket<T>() where T : Packet
    {
        RegisterPacket(typeof(T));
    }


    private void RegisterPacket(Type type)
    {
        if (type.IsAbstract || !type.IsSubclassOf(typeof(Packet))) return;
        Serializer serializer = null;
        Deserializer deserializer = null;

        var dict = new Dictionary<string, PropertyInfo>();
        var empty = Array.Empty<object>();

        foreach (var (prop, flag) in
            type.GetProperties(BindingFlags.NonPublic | BindingFlags.Instance).Select(p => (p, BindingFlags.NonPublic))
                .Concat(type.GetProperties(BindingFlags.Public | BindingFlags.Instance).Select(p => (p, BindingFlags.Public))))
        {
            dict.Add(prop.Name, prop);

            if (prop.IsDefined(typeof(IgnoreAttribute))) continue;
            if (flag == BindingFlags.NonPublic && !prop.IsDefined(typeof(ForceSerializeAttribute))) continue;

            var ver = prop.GetCustomAttribute<ProtocolVersionAttribute>();
            if (ver != null && ver.Version != Version) continue;

            var getter = prop.BuildDynamicGetter();
            var setter = prop.BuildDynamicSetter();
            var t = prop.PropertyType;

            Func<object, bool> condition = _ => true;

            var cond = prop.GetCustomAttribute<ConditionAttribute>();

            var shouldSerialize = (Client
                ? (object)prop.GetCustomAttribute<S2COnlyAttribute>()
                : prop.GetCustomAttribute<C2SOnlyAttribute>()) == null;
            var shouldDeserialize = (!Client
                ? (object)prop.GetCustomAttribute<S2COnlyAttribute>()
                : prop.GetCustomAttribute<C2SOnlyAttribute>()) == null && setter != null;

            if (cond != null)
            {
                var property = dict[cond.FieldName];
                var get2 = property.BuildDynamicGetter();
                // right here we cache a delegate to the getter.
                // calls to this delegate would be slower than direct calls but about 10 times faster than MethodBase.Invoke.
                if (cond.BitIndex == -1)
                    condition = o => (bool)get2(o);
                else
                    condition = o => ((BitsByte)get2(o))[cond.BitIndex] == cond.Prediction;
            }

            IFieldSerializer ser;

            ser = RequestFieldSerializer(t, Version);
        serFound:

            if (ser is IConfigurable conf) 
                ser = (IFieldSerializer)conf.Configure(prop, Version);

            if (shouldSerialize)
                serializer += (o, bw) => { if (condition(o)) ser.Write(bw, getter(o)); };
            if (shouldDeserialize)
                deserializer += (o, br) => { if (condition(o)) setter(o, ser.Read(br)); };
        }

        var inst = Activator.CreateInstance(type);

        if (Client ? (type.GetCustomAttribute<S2COnlyAttribute>() == null) : (type.GetCustomAttribute<C2SOnlyAttribute>()) == null)
            serializers[type] = (bw, o) => serializer?.Invoke(o, bw);

        if ((!Client) ? (type.GetCustomAttribute<S2COnlyAttribute>() == null) : (type.GetCustomAttribute<C2SOnlyAttribute>()) == null)
        {
            if (inst is NetModulesPacket p)
            {
                moduledeserializers.Add(p.ModuleType, br =>
                {
                    var result = Activator.CreateInstance(type) as NetModulesPacket;
                    deserializer?.Invoke(result, br);
                    return result;
                });
            }
            else if (inst is Packet p2)
            {
                deserializers.Add(p2.Type, br =>
                {
                    var result = Activator.CreateInstance(type) as Packet;
                    deserializer?.Invoke(result, br);
                    return result;
                });
            }
        }
    }

    public bool Client { get; }
    public string Version { get; }


    public PacketSerializer(bool client, string version = "Terraria248")
    {
        Client = client;
        Version = version;
        LoadPackets();
    }

    public TextWriter ErrorLogger { get; set; } = Console.Out;

    public Packet Deserialize(BinaryReader br0)
    {
        var l = br0.ReadInt16();
        using var ms = new MemoryStream(br0.ReadBytes(l - 2));
        using var br = new BinaryReader(ms);
        Packet result = null;
        var msgid = (MessageID)br.ReadByte();
        if (msgid == MessageID.NetModules)
        {
            var moduletype = (NetModuleType)br.ReadInt16();
            if (moduledeserializers.TryGetValue(moduletype, out var f))
                result = f(br);
            else
                ErrorLogger.WriteLine($"[Warning] net module type = {moduletype} not defined, ignoring");
        }
        else if (deserializers.TryGetValue(msgid, out var f2))
            result = f2(br);
        else
            ErrorLogger.WriteLine($"[Warning] message type = {msgid} not defined, ignoring");

        if (br.BaseStream.Position != br.BaseStream.Length)
        {
            ErrorLogger.WriteLine($"[Warning] {br.BaseStream.Length - br.BaseStream.Position} not used when deserializing {(Client ? "S2C::" : "C2S::")}{result}");
        }
        return result;
    }

    public byte[] Serialize(Packet p)
    {
        using var ms = new MemoryStream();
        using var bw = new BinaryWriter(ms);
        bw.Write((short)0);

        if (serializers.TryGetValue(p.GetType(), out var f))
        {
            f(bw, p);
            var l = bw.BaseStream.Position;
            bw.BaseStream.Position = 0;
            bw.Write((short)l);
            var bs = ms.ToArray();
            return bs;
        }

        ErrorLogger.WriteLine($"[Warning] packet {p} not defined, ignoring");
        return Array.Empty<byte>();
    }

}
