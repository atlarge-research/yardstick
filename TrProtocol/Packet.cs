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
        byte ItemSlot { get; set; }
    }
    public interface INPCSlot
    {
        byte NPCSlot { get; set; }
    }
    public interface IProjSlot
    {
        byte ProjSlot { get; set; }
    }
    public abstract class NetModulesPacket : Packet
    {
        public abstract short ModuleType { get; }
    }
}
