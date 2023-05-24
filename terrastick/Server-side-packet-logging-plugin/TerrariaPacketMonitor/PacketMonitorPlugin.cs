using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Streams;
using System.Reflection;
using System.Text;
using Terraria;
using Terraria.DataStructures;
using Terraria.GameContent.Tile_Entities;
using TerrariaApi.Server;
using System.Diagnostics;

namespace TerrariaPacketMonitor
{
    [ApiVersion(2, 1)]
    public class PacketMonitorPlugin : TerrariaPlugin
    {
        private static Stopwatch stopwatch;
        private  int i = 0;
        public override string Author => "Abhilash Balaji";
        public override string Description => "Dumps packet data to stream";
        public override string Name => "Packet Monitor";
        public override Version Version => Assembly.GetExecutingAssembly().GetName().Version;
       
        public TextWriter OutputStream { get; set; }

        public PacketMonitorPlugin(Main game) : base(game)
        {
            Order = -1;
        }

        public override void Initialize()
        {

            Directory.CreateDirectory(Path.Combine(TShockAPI.TShock.SavePath, "PacketLogs"));

            FileStream fileStream = new FileStream(Path.Combine(TShockAPI.TShock.SavePath, "PacketLogs", GetFileName()), FileMode.Create, FileAccess.Write, FileShare.Read);
            OutputStream = new StreamWriter(fileStream);
            //OutputStream = Console.Out;
            stopwatch = new Stopwatch();

            ServerApi.Hooks.NetGetData.Register(this, OnGetData, -1);
            ServerApi.Hooks.NetSendData.Register(this, OnSendData, -1);
            ServerApi.Hooks.GamePostUpdate.Register(this, (EventArgs args) =>
            {
                // end of game update
                stopwatch.Stop();

                SendOutput($"GAME UPDATE TIME : {stopwatch.ElapsedMilliseconds}");
                stopwatch.Reset();
            }, -1);
            ServerApi.Hooks.GameUpdate.Register(this, (args) =>
            {
                if (stopwatch != null && stopwatch.IsRunning)
                {
                    throw new InvalidOperationException("Stopwatch is already running.");
                }
                //


                stopwatch.Start();
                //SendOutput("start GAMEUPDATE");
            }, -1);
          
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                OutputStream.Dispose();
            }
            base.Dispose(disposing);
        }

        string GetFileName()
        {
            return DateTime.UtcNow.ToString("yyyy-MM-dd.hh.mm.ss") + "_out.log";
        }

        void SendOutput(string output)
        {
            OutputStream.WriteLine($"{DateTime.Now}: {output}");
        }

        
        void OnGetData(GetDataEventArgs args)
        {
            PacketTypes type = args.MsgID;

            List<PacketTypes> spamPackets = new List<PacketTypes> { PacketTypes.PlayerHp, PacketTypes.NpcTalk, PacketTypes.Zones };
            if (!spamPackets.Contains(type))
            {
                SendOutput($"[Recv] {(byte)type} ({type}) from: {args.Msg.whoAmI} ({Main.player[args.Msg.whoAmI].name})");
            }

            if (type == PacketTypes.PlaceTileEntity)
            {
                using (var data = new MemoryStream(args.Msg.readBuffer, args.Index, args.Length - 1))
                {
                    short x = data.ReadInt16();
                    short y = data.ReadInt16();
                    byte teType = data.ReadInt8();

                    SendOutput($"\t\t[Recv] TEpl @ ({x}, {y}), type: {teType}");
                }
            }

            if (type==PacketTypes.PlayerUpdate)
            {
                using(var data = new MemoryStream(args.Msg.readBuffer,args.Index,args.Length-1))
                {
                    /*
                     * Server <-> Client (Sync)
Size	Description	Type	Notes
1	Player ID	Byte	-
1	Control	Byte	BitFlags: 1 = ControlUp, 2 = ControlDown, 4 = ControlLeft, 8 = ControlRight, 16 = ControlJump, 32 = ControlUseItem, 64 = Direction
1	Pulley	Byte	BitFlags: 1 = Pulley Enabled, 2 = Direction, 4 = UpdateVelocity, 8 = VortexStealthActive, 16 = GravityDirection, 32 = ShieldRaised
1	Misc	Byte	BitFlags: 1 = HoveringUp, 2 = VoidVaultEnabled, 4 = Sitting, 8 = DownedDD2Event, 16 = IsPettingAnimal, 32 = IsPettingSmallAnimal, 64 = UsedPotionofReturn, 128 = HoveringDown
1	SleepingInfo	Byte	BitFlags: 1 = IsSleeping
1	Selected Item	Byte	-
4	Position X	Single	-
4	Position Y	Single	-
4	Velocity X	Single	Not sent if UpdateVelocity is not set
4	Velocity Y	Single	Not sent if UpdateVelocity is not set
4	Original Position X	Single	Original Position for Potion of Return, only sent if UsedPotionofReturn flag is true
4	Original Position Y	Single	Original Position for Potion of Return, only sent if UsedPotionofReturn flag is true
4	Home Position X	Single	Home Position for Potion of Return, only sent if UsedPotionofReturn flag is true
4	Home Position Y	Single	Home Position for Potion of Return, only sent if UsedPotionofReturn flag is true
                     */

                    byte id = data.ReadInt8();
                    byte control = data.ReadInt8();
                    byte pulley = data.ReadInt8();
                    byte Misc = data.ReadInt8();
                    byte sleeping = data.ReadInt8();
                    byte selectedItem = data.ReadInt8();
                    float x = data.ReadSingle();
                    float y = data.ReadSingle();
                    float velX = 0;
                    float velY = 0;
                    float origX = 0;
                    float origY = 0;
                    float homeX = 0;
                    float homeY = 0;

                    // print out player id and update x and y
                    SendOutput($"\t\t[Recv] PlayerUpdate @ {id} ({x}, {y})");

                }
            }

            if (type == PacketTypes.PlaceObject)
            {
                using (var data = new MemoryStream(args.Msg.readBuffer, args.Index, args.Length - 1))
                {
                    short x = data.ReadInt16();
                    short y = data.ReadInt16();
                    short objType = data.ReadInt16();
                    short style = data.ReadInt16();

                    SendOutput($"\t\t[Recv] OBJpl @ ({x}, {y}), type: {objType}, style: {style}");
                }
            }

            if (type == PacketTypes.Tile)
            {
                using (var data = new MemoryStream(args.Msg.readBuffer, args.Index, args.Length - 1))
                {
                    byte action = data.ReadInt8();
                    short x = data.ReadInt16();
                    short y = data.ReadInt16();
                    short var1 = data.ReadInt16();
                    byte var2 = data.ReadInt8();

                    bool fail = var1 == 1;

                    SendOutput($"\t\t [Recv] Tile Edit @ ({x}, {y}), action: {action}, var1: {var1}, var2: {var2}, fail: {fail}");
                }
            }

            if (type == PacketTypes.TileSendSquare)
            {
                using (var data = new MemoryStream(args.Msg.readBuffer, args.Index, args.Length - 1))
                {
                    ushort data1 = data.ReadUInt16();
                    short size = (short)(data1 & 0x7FFF);
                    bool hasChangeType = (short)(size & 0x8000) != 0;
                    byte tyleChangeType = 0;
                    if (hasChangeType) { tyleChangeType = data.ReadInt8(); }
                    short x = data.ReadInt16();
                    short y = data.ReadInt16();

                    SendOutput($"[Recv] Tile Square @ ({x}, {y}), data1: {data1}, size: {size}, hasChangeType: {hasChangeType}");
                }
            }
        }

        void OnSendData(SendDataEventArgs args)
        {
            PacketTypes type = args.MsgId;

            List<PacketTypes> spamPackets = new List<PacketTypes> { PacketTypes.TileSendSquare, PacketTypes.PlayerUpdate, PacketTypes.PlayerHp, PacketTypes.NpcTalk, PacketTypes.ProjectileDestroy, PacketTypes.ProjectileNew, PacketTypes.NpcUpdate, PacketTypes.Zones, PacketTypes.ItemDrop };
            if (!spamPackets.Contains(type))
            {
                SendOutput($"[Send] {(byte)type} ({type}) ign: {args.ignoreClient} ({(args.ignoreClient == -1 ? "-" : Main.player[args.ignoreClient].name)}) | rem: {args.remoteClient} ({(args.remoteClient == -1 ? "-" : Main.player[args.remoteClient].name)})");
            }
            else
            {
                return;
            }

            if (type == PacketTypes.UpdateTileEntity)
            {
                int id = args.number;
                bool exists = TileEntity.ByID.ContainsKey(id);
                StringBuilder sb = new StringBuilder();

                sb.Append($"\t\t[Send] TEupd. Entity ID: {id}. Remove entity: {!exists}.");

                if (exists)
                {
                    TEItemFrame iframe = (TEItemFrame)TileEntity.ByID[id];
                    sb.Append($"\n\t\t  Type: {iframe.type}. Position: ({iframe.Position.X}, {iframe.Position.Y})");
                    sb.Append($"\n\t\t  Item details: Type: {iframe.item?.type}. Stack: {iframe.item?.stack}");
                }

                SendOutput(sb.ToString());
            }

            if (type == PacketTypes.Tile)
            {
                byte action = (byte)args.number;
                short x = (short)args.number2;
                short y = (short)args.number3;
                short var1 = (short)args.number4;
                byte var2 = (byte)args.number5;

                SendOutput($"\t\t [Send] Tile Edit @ ({x}, {y}), action: {action}, var1: {var1}, var2: {var2}, fail: {var1 == 1}");
            }

            if (type == PacketTypes.TileSendSquare)
            {
                int size = args.number;
                int tileX = (int)args.number2;
                int tileY = (int)args.number3;

                if (size < 0) size = 0;

                if (tileX < size) tileX = size;
                if (tileX >= Main.maxTilesX + size) { tileX = Main.maxTilesX - size - 1; }

                if (tileY < size) tileY = size;
                if (tileY >= Main.maxTilesY + size) { tileY = Main.maxTilesY - size - 1; }

                int adjustedSize1 = size & 0x7FFF;
                int adjustedSize2 = ((size & 0x7FFF) | 0x8000);

                SendOutput($"[Send] Tile Square @ ({tileX}, {tileY}), size: {size}, adjustedSize1: {adjustedSize1:x4}, adjustedSize2: {adjustedSize2:x4}, hasChangeType: {args.number5 != 0}");
            }
        }
    }
}
