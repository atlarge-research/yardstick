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
        public bool pred;
        public ConditionAttribute(string field, byte bit, bool pred=true)
        {
            this.bit = bit;
            this.field = field;
            this.pred = pred;
        }
    }
}
