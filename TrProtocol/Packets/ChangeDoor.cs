using System;
using TrProtocol.Models;

namespace TrProtocol.Packets
{
    public class ChangeDoor : Packet
    {
        public override MessageID Type => MessageID.ChangeDoor;
        public bool ChangeType { get; set; }
        public ShortPosition Position { get; set; }
    }
}
