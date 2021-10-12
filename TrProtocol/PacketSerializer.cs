using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using TrProtocol.Models;
using TrProtocol.Packets;

namespace TrProtocol
{
    public partial class PacketSerializer
    {
        private delegate void Serializer(object o, BinaryWriter bw);
        private delegate void Deserializer(object o, BinaryReader br);

        private Dictionary<Type, Action<BinaryWriter, Packet>> serializers = new();

        private Dictionary<MessageID, Func<BinaryReader, Packet>> deserializers = new();
        private Dictionary<NetModuleType, Func<BinaryReader, NetModulesPacket>> moduledeserializers = new();

        public void LoadPackets(Assembly asm)
        {
            foreach (var type in asm.GetTypes())
            {
                if (type.IsAbstract || !type.IsSubclassOf(typeof(Packet))) continue;
                Serializer serializer = null;
                Deserializer deserializer = null;

                var dict = new Dictionary<string, PropertyInfo>();
                var empty = Array.Empty<object>();

                foreach (var prop in type.GetProperties())
                {
                    dict.Add(prop.Name, prop);

                    if (prop.IsDefined(typeof(IgnoreAttribute))) continue;

                    var get = prop.GetMethod;
                    var set = prop.SetMethod;
                    var t = prop.PropertyType;

                    Func<object, bool> condition = _ => true;

                    var cond = prop.GetCustomAttribute<ConditionAttribute>();

                    var shouldSerialize = (client
                        ? (object)prop.GetCustomAttribute<S2COnlyAttribute>()
                        : prop.GetCustomAttribute<C2SOnlyAttribute>()) == null;
                    var shouldDeserialize = (!client
                        ? (object)prop.GetCustomAttribute<S2COnlyAttribute>()
                        : prop.GetCustomAttribute<C2SOnlyAttribute>()) == null && set != null;
                    
                    if (cond != null)
                    {
                        var get2 = dict[cond.field].GetMethod;
                        if (cond.bit == -1)
                            condition = o => ((bool) get2.Invoke(o, empty));
                        else
                            condition = o => ((BitsByte)get2.Invoke(o, empty))[cond.bit] == cond.pred;
                    }


                    var attr = t.GetCustomAttribute<SerializerAttribute>();
                    IFieldSerializer ser;
                    if (attr != null) ser = attr.serializer;
                    else if (!fieldSerializers.TryGetValue(t, out ser))
                        throw new Exception("No valid serializer for type: " + t.FullName);
                    if (ser is IConfigurable conf) ser = conf.Configure(prop);

                    if (shouldSerialize)
                        serializer += (o, bw) => { if (condition(o)) ser.Write(bw, get.Invoke(o, empty)); };
                    if (shouldDeserialize)
                        deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new [] { ser.Read(br) }); };
                }

                var inst = Activator.CreateInstance(type);

                if (client ? (type.GetCustomAttribute<S2COnlyAttribute>() == null) : (type.GetCustomAttribute<C2SOnlyAttribute>()) == null)
                    serializers[type] = (bw, o) => serializer?.Invoke(o, bw);

                if ((!client) ? (type.GetCustomAttribute<S2COnlyAttribute>() == null) : (type.GetCustomAttribute<C2SOnlyAttribute>()) == null)
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
        }

        private readonly bool client;

        public PacketSerializer(bool client)
        {
            this.client = client;
            LoadPackets(Assembly.GetExecutingAssembly());
        }
        
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
                    Console.WriteLine($"[Warning] net module type = {moduletype} not defined, ignoring");
            }
            else if (deserializers.TryGetValue(msgid, out var f2))
                result = f2(br);
            else
                Console.WriteLine($"[Warning] message type = {msgid} not defined, ignoring");

            if (br.BaseStream.Position != br.BaseStream.Length)
            {
                Console.WriteLine($"[Warning] {br.BaseStream.Length - br.BaseStream.Position} not used when deserializing {(client ? "S2C::" : "C2S::")}{result}");
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
                return ms.ToArray();
            }
            
            Console.WriteLine($"[Warning] packet {p} not defined, ignoring");
            return Array.Empty<byte>();
        }

    }
}
