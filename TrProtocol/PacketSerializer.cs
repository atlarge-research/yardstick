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
    public class PacketSerializer
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

                    var get = prop.GetMethod;
                    var set = prop.SetMethod;
                    var t = prop.PropertyType;

                    Func<object, bool> condition = _ => true;

                    var cond = prop.GetCustomAttribute<ConditionAttribute>();

                    var shouldSerialize = (client
                        ? (Attribute)prop.GetCustomAttribute<S2COnlyAttribute>()
                        : prop.GetCustomAttribute<C2SOnlyAttribute>()) == null;
                    var shouldDeserialize = (!client
                        ? (Attribute)prop.GetCustomAttribute<S2COnlyAttribute>()
                        : prop.GetCustomAttribute<C2SOnlyAttribute>()) == null && set != null;
                    
                    if (cond != null)
                    {
                        var get2 = dict[cond.field].GetMethod;
                        if (cond.integer != null)
                            condition = o =>
                                (long) Convert.ChangeType(get2.Invoke(o, empty), typeof(long)) == cond.integer ^ cond.pred;
                        else if (cond.bit == -1)
                            condition = o => ((bool) get2.Invoke(o, empty));
                        else
                            condition = o => ((BitsByte)get2.Invoke(o, empty))[cond.bit] == cond.pred;
                    }


                    if (t == typeof(bool))
                    {
                        if (shouldSerialize)
                            serializer += (o, bw) => { if (condition(o)) bw.Write((bool)get.Invoke(o, empty)); };
                        if (shouldDeserialize)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadBoolean() }); };
                    }
                    else if (t == typeof(sbyte))
                    {
                        if (shouldSerialize)
                            serializer += (o, bw) => { if (condition(o)) bw.Write((sbyte)get.Invoke(o, empty)); };
                        if (shouldDeserialize)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadSByte() }); };
                    }
                    else if (t == typeof(byte))
                    {
                        if (shouldSerialize)
                            serializer += (o, bw) => { if (condition(o)) bw.Write((byte)get.Invoke(o, empty)); };
                        if (shouldDeserialize)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadByte() }); };
                    }
                    else if (t == typeof(short))
                    {
                        if (shouldSerialize)
                            serializer += (o, bw) => { if (condition(o)) bw.Write((short)get.Invoke(o, empty)); };
                        if (shouldDeserialize)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadInt16() }); };
                    }
                    else if (t == typeof(ushort))
                    {
                        if (shouldSerialize)
                            serializer += (o, bw) => { if (condition(o)) bw.Write((ushort)get.Invoke(o, empty)); };
                        if (shouldDeserialize)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadUInt16() }); };
                    }
                    else if (t == typeof(int))
                    {
                        if (shouldSerialize)
                            serializer += (o, bw) => { if (condition(o)) bw.Write((int)get.Invoke(o, empty)); };
                        if (shouldDeserialize)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadInt32() }); };
                    }
                    else if (t == typeof(uint))
                    {
                        if (shouldSerialize)
                            serializer += (o, bw) => { if (condition(o)) bw.Write((uint)get.Invoke(o, empty)); };
                        if (shouldDeserialize)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadUInt32() }); };
                    }
                    else if (t == typeof(string))
                    {
                        if (shouldSerialize)
                            serializer += (o, bw) => { if (condition(o)) bw.Write((string)get.Invoke(o, empty)); };
                        if (shouldDeserialize)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadString() }); };
                    }
                    else if (t == typeof(float))
                    {
                        if (shouldSerialize)
                            serializer += (o, bw) => { if (condition(o)) bw.Write((float)get.Invoke(o, empty)); };
                        if (shouldDeserialize)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadSingle() }); };
                    }
                    else if (t == typeof(ushort[]))
                    {
                        if (shouldSerialize)
                            serializer += (o, bw) =>
                        {
                            if (!condition(o)) return;
                            foreach (var x in (ushort[])get.Invoke(o, empty))
                                bw.Write(x);

                        };
                        var n = prop.GetCustomAttribute<ArraySizeAttribute>().size;
                        if (shouldDeserialize)
                        {
                            deserializer += (o, br) =>
                            {
                                if (!condition(o)) return;
                                var t = new ushort[n];
                                for (int i = 0; i < n; ++i) t[i] = br.ReadUInt16();
                                set.Invoke(o, new object[] { t });
                            };
                        }
                    }
                    else if (t == typeof(short[]))
                    {
                        if (shouldSerialize)
                            serializer += (o, bw) =>
                        {
                            if (!condition(o)) return;
                            foreach (var x in (short[])get.Invoke(o, empty))
                                bw.Write(x);

                        };
                        var n = prop.GetCustomAttribute<ArraySizeAttribute>().size;
                        if (shouldDeserialize)
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
                        if (shouldSerialize)
                            serializer += (o, bw) => { if (condition(o)) bw.Write((byte[])get.Invoke(o, empty)); };
                        if (shouldDeserialize)
                            deserializer += (o, br) => { if (condition(o)) set.Invoke(o, new object[] { br.ReadBytes((int)(br.BaseStream.Length - br.BaseStream.Position)) }); };
                    }
                    else
                    {
                        var attr = t.GetCustomAttribute<SerializerAttribute>();
                        IFieldSerializer ser;
                        if (attr != null) ser = attr.serializer;
                        else if (!fieldSerializers.TryGetValue(t, out ser))
                            throw new Exception("No valid serializer for type: " + t.FullName);

                        if (shouldSerialize)
                            serializer += (o, bw) => { if (condition(o)) ser.Write(bw, get.Invoke(o, empty)); };
                        if (shouldDeserialize)
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
                Console.WriteLine($"[Warning] {br.BaseStream.Length - br.BaseStream.Position} not used when serializing {result}");
            }
            return result;
        }

        private Dictionary<Type, IFieldSerializer> fieldSerializers = new();
        public void RegisterSerializer<T>(IFieldSerializer serializer)
        {
            fieldSerializers.Add(typeof(T), serializer);
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
