using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;

namespace TrProtocol.Models
{
    [StructLayout(LayoutKind.Sequential)]
    public struct Buff
    {
        public ushort BuffType { get; set; }
        public short BuffTime { get; set; }
    }
}
