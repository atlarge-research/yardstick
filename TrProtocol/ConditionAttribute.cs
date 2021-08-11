using System;
using TrProtocol.Models;

namespace TrProtocol
{
    [AttributeUsage(AttributeTargets.Class | AttributeTargets.Property)]
    public sealed class S2COnlyAttribute : Attribute
    {

    }

    [AttributeUsage(AttributeTargets.Class | AttributeTargets.Property)]
    public sealed class C2SOnlyAttribute : Attribute
    {

    }


    [AttributeUsage(AttributeTargets.Property)]
    public sealed class ArraySizeAttribute : Attribute
    {
        public int size;

        public ArraySizeAttribute(int size)
        {
            this.size = size;
        }
    }
    [AttributeUsage(AttributeTargets.Property)]
    public sealed class ConditionAttribute : Attribute
    {
        public string field;
        public sbyte bit;
        public bool pred;
        public long? integer;

        public ConditionAttribute(string field, sbyte bit = -1, bool pred = true)
        {
            this.bit = bit;
            this.field = field;
            this.pred = pred;
        }
        public ConditionAttribute(string field, long integer, bool inv = false)
        {
            this.field = field;
            this.integer = integer;
            this.pred = inv;
        }
    }
}
