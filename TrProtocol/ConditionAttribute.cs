using System;
using TrProtocol.Models;

namespace TrProtocol
{
    [AttributeUsage(AttributeTargets.Class)]
    public sealed class S2COnlyAttribute : Attribute
    {

    }

    [AttributeUsage(AttributeTargets.Class)]
    public sealed class C2SOnlyAttribute : Attribute
    {

    }

    [AttributeUsage(AttributeTargets.Property)]
    public sealed class ConditionAttribute : Attribute
    {
        public string field;
        public byte bit;
        public ConditionAttribute(string field, byte bit)
        {
            this.bit = bit;
            this.field = field;
        }
    }
}
