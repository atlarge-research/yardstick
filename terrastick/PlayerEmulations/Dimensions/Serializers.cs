﻿using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Dimensions.Packets;
using TrProtocol;

namespace Dimensions
{
    internal static class Serializers
    {
        public static readonly PacketSerializer clientSerializer = new(true, Program.config.protocolVersion);
        public static readonly PacketSerializer serverSerializer = new(false, Program.config.protocolVersion);

        static Serializers()
        {
            clientSerializer.RegisterPacket<DimensionUpdate>();
            serverSerializer.RegisterPacket<DimensionUpdate>();
        }
    }
}
