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
    public class HitSwitch : Packet
    {
        public override MessageID Type => MessageID.HitSwitch;
        public ShortPosition Position { get; set; }
    }
    public class NPCHome : Packet, INPCSlot
    {
        public override MessageID Type => MessageID.NPCHome;
        public short NPCSlot { get; set; }
        public ShortPosition Position { get; set; }
    }
    public class SpawnBoss : Packet, IOtherPlayerSlot
    {
        public override MessageID Type => MessageID.SpawnBoss;
        public byte OtherPlayerSlot { get; set; }
        public byte HighBitOfPlayerIsAlwaysZero { get; set; } = 0;
        public short NPCType { get; set; }
    }
    public class Dodge : Packet, IPlayerSlot
    {
        public override MessageID Type => MessageID.Dodge;
        public byte PlayerSlot { get; set; }
        public byte DodgeType { get; set; }
    }
    public class PaintTile : Packet
    {
        public override MessageID Type => MessageID.PaintTile;
        public ShortPosition Position { get; set; }
        public byte Color { get; set; }
    }
}
