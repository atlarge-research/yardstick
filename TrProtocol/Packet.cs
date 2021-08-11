using System;
using TrProtocol.Models;

namespace TrProtocol
{
    public abstract class Packet
    {
        public abstract MessageID Type { get; }
    }
    public interface IPlayerSlot
    {
        byte PlayerSlot { get; set; }
    }
    public interface IOtherPlayerSlot
    {
        byte OtherPlayerSlot { get; set; }
    }
    public interface IItemSlot
    {
        short ItemSlot { get; set; }
    }
    public interface INPCSlot
    {
        short NPCSlot { get; set; }
    }
    public interface IProjSlot
    {
        short ProjSlot { get; set; }
    }
    public abstract class NetModulesPacket : Packet
    {
        public abstract NetModuleType ModuleType { get; }
    }
}
