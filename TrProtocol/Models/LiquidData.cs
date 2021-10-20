using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TrProtocol.Models
{
    public partial struct LiquidData
    {
        public ushort TotalChanges { get; set; }
        public LiquidChange[] LiquidChanges { get; set; }
    }
}
