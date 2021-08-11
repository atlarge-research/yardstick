using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;
using TrProtocol.Models;

namespace TrProtocol
{
    public class PacketSerializer
    {
        private delegate void Serializer(object o, BinaryWriter bw);
        private delegate void Deserializer(object o, BinaryReader br);

        private Dictionary<Type, Action<BinaryWriter, Packet>> serializers = new();

        private Dictionary<MessageID, Func<BinaryReader, Packet>> deserializers = new();
        private Dictionary<short, Func<BinaryReader, NetModulesPacket>> moduledeserializers = new();

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

                    var get = prop.GetMethod;
                    var set = prop.SetMethod;
                    var t = prop.PropertyType;

                    Func<object, bool> condition = _ => true;

                    var cond = prop.GetCustomAttribute<ConditionAttribute>();

                    if ((client
                        ? (Attribute)prop.GetCustomAttribute<S2COnlyAttribute>()
                        : prop.GetCustomAttribute<C2SOnlyAttribute>()) != null)
                        continue;

                    if (cond != null)
                    {
                        var get2 = dict[cond.field].GetMethod;
                        condition = o => ((BitsByte)get2.Invoke(o, empty))[cond.bit] == cond.pred;
                    }


                    if (t == typeof(int))
                    {
                        serializer += (o, bw) => { if (condition(o)) bw.Write((int)get.Invoke(o, empty)); };
                        if (set != null)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadInt32() }); };
                    }
                    else if (t == typeof(bool))
                    {
                        serializer += (o, bw) => { if (condition(o)) bw.Write((bool)get.Invoke(o, empty)); };
                        if (set != null)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadBoolean() }); };
                    }
                    else if (t == typeof(sbyte))
                    {
                        serializer += (o, bw) => { if (condition(o)) bw.Write((sbyte)get.Invoke(o, empty)); };
                        if (set != null)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadSByte() }); };
                    }
                    else if (t == typeof(byte))
                    {
                        serializer += (o, bw) => { if (condition(o)) bw.Write((byte)get.Invoke(o, empty)); };
                        if (set != null)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadByte() }); };
                    }
                    else if (t == typeof(short))
                    {
                        serializer += (o, bw) => { if (condition(o)) bw.Write((short)get.Invoke(o, empty)); };
                        if (set != null)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadInt16() }); };
                    }
                    else if (t == typeof(ushort))
                    {
                        serializer += (o, bw) => { if (condition(o)) bw.Write((ushort)get.Invoke(o, empty)); };
                        if (set != null)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadUInt16() }); };
                    }
                    else if (t == typeof(string))
                    {
                        serializer += (o, bw) => { if (condition(o)) bw.Write((string)get.Invoke(o, empty)); };
                        if (set != null)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadString() }); };
                    }
                    else if (t == typeof(float))
                    {
                        serializer += (o, bw) => { if (condition(o)) bw.Write((float)get.Invoke(o, empty)); };
                        if (set != null)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadSingle() }); };
                    }
                    else if (t == typeof(short[]))
                    {
                        serializer += (o, bw) =>
                        {
                            if (!condition(o)) return;
                            foreach (var x in (short[])get.Invoke(o, empty))
                                bw.Write(x);

                        };
                        var n = t.GetCustomAttribute<ArraySizeAttribute>().size;
                        if (set != null)
                        {
                            deserializer += (o, br) =>
                            {
                                if (!condition(o)) return;
                                var t = new short[n];
                                for (int i = 0; i < n; ++i) t[i] = br.ReadInt16();
                                set.Invoke(o, new object[] {t});
                            };
                        }
                    }
                    else if (t == typeof(byte[]))
                    {
                        serializer += (o, bw) => { if (condition(o)) bw.Write((byte[])get.Invoke(o, empty)); };
                        if (set != null)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadBytes((int)(br.BaseStream.Length - br.BaseStream.Position)) }); };
                    }
                    else
                    {
                        var ser = t.GetCustomAttribute<SerializerAttribute>().serializer;

                        serializer += (o, bw) => { if (condition(o)) ser.Write(bw, get.Invoke(o, empty)); };
                        if (set != null)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { ser.Read(br) }); };
                    }
                }

                var inst = Activator.CreateInstance(type);

                if (client ? (type.GetCustomAttribute<S2COnlyAttribute>() == null) : (type.GetCustomAttribute<C2SOnlyAttribute>()) == null)
                    serializers[type] = (bw, o) => serializer?.Invoke(o, bw);

                if ((!client) ? (type.GetCustomAttribute<S2COnlyAttribute>() == null) : (type.GetCustomAttribute<C2SOnlyAttribute>()) == null)
                {
                    if (inst is NetModulesPacket p)
                    {
                        moduledeserializers[p.ModuleType] = br =>
                        {
                            var result = Activator.CreateInstance(type) as NetModulesPacket;
                            deserializer?.Invoke(result, br);
                            return result;
                        };
                    }
                    else if (inst is Packet p2)
                    {
                        deserializers[p2.Type] = br =>
                        {
                            var result = Activator.CreateInstance(type) as Packet;
                            deserializer?.Invoke(result, br);
                            return result;
                        };
                    }
                }
                    
            }
        }

        private bool client;

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

            var msgid = (MessageID)br.ReadByte();
            if (msgid == MessageID.NetModules)
            {
                var moduletype = br.ReadInt16();
                if (moduledeserializers.TryGetValue(moduletype, out var f))
                    return f(br);
                else
                    Console.WriteLine($"[Warning] net module type = {moduletype} not defined, ignoring");
            }
            else if (deserializers.TryGetValue(msgid, out var f2))
                return f2(br);
            else
                Console.WriteLine($"[Warning] message type = {msgid} not defined, ignoring");
            return null;
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
            else
                Console.WriteLine($"[Warning] packet {p} not defined, ignoring");
            return Array.Empty<byte>();
        }
    }
}
