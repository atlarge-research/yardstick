using TrProtocol.Models;

namespace TrProtocol.Packets
{
    public class NPCHome : Packet, INPCSlot
    {
        public override MessageID Type => MessageID.NPCHome;
        public short NPCSlot { get; set; }
        public ShortPosition Position { get; set; }
    }
}