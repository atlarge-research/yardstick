using TrProtocol.Models;

namespace TrProtocol.Packets
{
    public class ChestUpdates : Packet
    {
        public override MessageID Type => MessageID.ChestUpdates;
        public byte Operation { get; set; }
        public ShortPosition Position { get; set; }
        //FIXME: DONT NO WHAT IT IS
        public short Unknown1 { get; set; }
        public short Unknown2 { get; set; }
    }
}