using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TrProtocol.Packets
{
    public class RequestLucyPopup : Packet
    {
        public override MessageID Type => MessageID.RequestLucyPopup;
        public MessageSource Source { get; set; }
        public byte Variation { get; set; }
        public Vector2 Velocity { get; set; }
        public Position Position { get; set; }
    }
    public class SyncItemsWithShimmer : Packet, IItemSlot
    {
        public override MessageID Type => MessageID.SyncItemsWithShimmer;
        public short ItemSlot { get; set; }
        public Vector2 Position { get; set; }
        public Vector2 Velocity { get; set; }
        public short Stack { get; set; }
        public byte Prefix { get; set; }
        public byte Owner { get; set; }
        public short ItemType { get; set; }
        public bool Shimmered { get; set; }
        public float ShimmerTime { get; set; }
    }

    public class SyncLoadout : Packet, IPlayerSlot, ILoadOutSlot
    {
        public override MessageID Type => MessageID.SyncLoadout;
        public byte PlayerSlot { get; set; }
        public byte LoadOutSlot { get; set; }
        public ushort AccessoryVisibility { get; set; }
    }

    public class SyncItemCannotBeTakenByEnemies : Packet, IItemSlot
    {
        public override MessageID Type => MessageID.SyncItemCannotBeTakenByEnemies;
        public short ItemSlot { get; set; }
        public Vector2 Position { get; set; }
        public Vector2 Velocity { get; set; }
        public short Stack { get; set; }
        public byte Prefix { get; set; }
        public byte Owner { get; set; }
        public byte TimeLeftInWhichTheItemCannotBeTakenByEnemies { get; set; }
    }
}
