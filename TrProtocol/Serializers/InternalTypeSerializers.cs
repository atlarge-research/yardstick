using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;

namespace TrProtocol
{
    public partial class PacketSerializer
    {
        static PacketSerializer()
        {
            RegisterSerializer(new ByteSerializer());
            RegisterSerializer(new SByteSerializer());
            RegisterSerializer(new ShortSerializer());
            RegisterSerializer(new UShortSerializer());
            RegisterSerializer(new IntSerializer());
            RegisterSerializer(new UIntSerializer());
            RegisterSerializer(new LongSerializer());
            RegisterSerializer(new ULongSerializer());
            RegisterSerializer(new FloatSerializer());
            RegisterSerializer(new StringSerializer());

            RegisterSerializer(new ArraySerializer<short>());
            RegisterSerializer(new ArraySerializer<ushort>());
            RegisterSerializer(new ArraySerializer<int>());
            RegisterSerializer(new ArraySerializer<uint>());
            RegisterSerializer(new ByteArraySerializer());
        }

        private static readonly Dictionary<Type, IFieldSerializer> fieldSerializers = new();
        private static void RegisterSerializer<T>(FieldSerializer<T> serializer)
        {
            fieldSerializers.Add(typeof(T), serializer);
        }

        private class ByteSerializer : FieldSerializer<byte>
        {
            protected override byte _Read(BinaryReader br) => br.ReadByte();
            protected override void _Write(BinaryWriter bw, byte t) => bw.Write(t);
        }
        private class SByteSerializer : FieldSerializer<sbyte>
        {
            protected override sbyte _Read(BinaryReader br) => br.ReadSByte();
            protected override void _Write(BinaryWriter bw, sbyte t) => bw.Write(t);
        }
        private class ShortSerializer : FieldSerializer<short>
        {
            protected override short _Read(BinaryReader br) => br.ReadInt16();
            protected override void _Write(BinaryWriter bw, short t) => bw.Write(t);
        }
        private class UShortSerializer : FieldSerializer<ushort>
        {
            protected override ushort _Read(BinaryReader br) => br.ReadUInt16();
            protected override void _Write(BinaryWriter bw, ushort t) => bw.Write(t);
        }
        private class IntSerializer : FieldSerializer<int>
        {
            protected override int _Read(BinaryReader br) => br.ReadInt32();
            protected override void _Write(BinaryWriter bw, int t) => bw.Write(t);
        }
        private class UIntSerializer : FieldSerializer<uint>
        {
            protected override uint _Read(BinaryReader br) => br.ReadUInt32();
            protected override void _Write(BinaryWriter bw, uint t) => bw.Write(t);
        }
        private class LongSerializer : FieldSerializer<long>
        {
            protected override long _Read(BinaryReader br) => br.ReadInt64();
            protected override void _Write(BinaryWriter bw, long t) => bw.Write(t);
        }
        private class ULongSerializer : FieldSerializer<ulong>
        {
            protected override ulong _Read(BinaryReader br) => br.ReadUInt64();
            protected override void _Write(BinaryWriter bw, ulong t) => bw.Write(t);
        }

        private class FloatSerializer : FieldSerializer<float>
        {
            protected override float _Read(BinaryReader br) => br.ReadSingle();
            protected override void _Write(BinaryWriter bw, float t) => bw.Write(t);
        }

        private class StringSerializer : FieldSerializer<string>
        {
            protected override string _Read(BinaryReader br) => br.ReadString();
            protected override void _Write(BinaryWriter bw, string t) => bw.Write(t);
        }

        private class ByteArraySerializer : FieldSerializer<byte[]>
        {
            protected override byte[] _Read(BinaryReader br)
            {
                return br.ReadBytes((int)(br.BaseStream.Length - br.BaseStream.Position));
            }

            protected override void _Write(BinaryWriter bw, byte[] t)
            {
                bw.Write(t);
            }
        }

        private class ArraySerializer<T> : FieldSerializer<T[]>, IConfigurable
        {
            private readonly int size;
            private readonly IFieldSerializer @base;
            public ArraySerializer() : this(0)
            {

            }

            private ArraySerializer(int size)
            {
                this.size = size;
                this.@base = fieldSerializers[typeof(T)];
            }

            protected override T[] _Read(BinaryReader br)
            {
                var t = new T[size];
                for (var i = 0; i < size; ++i) t[i] = (T)@base.Read(br);
                return t;
            }

            protected override void _Write(BinaryWriter bw, T[] t)
            {
                foreach (var x in t)
                    @base.Write(bw, x);
            }

            public IFieldSerializer Configure(PropertyInfo prop)
            {
                return new ArraySerializer<T>(prop.GetCustomAttribute<ArraySizeAttribute>().size);
            }
        }
    }
}