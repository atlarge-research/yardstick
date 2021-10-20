using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TrProtocol.Models
{
    public struct LiquidChange
    {
        public ShortPosition Position { get; set; }
        public byte LiquidAmount { get; set; }
        /// <summary>
        /// 1 = Water, 2 = Lava, 3 = Honey
        /// </summary>
        public byte LiquidType { get; set; }
    }
}
