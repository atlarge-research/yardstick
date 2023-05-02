using TrProtocol;
using TrProtocol.Packets;

namespace Dimensions.Core;

public class ItemHandler : ClientHandler
{
    private const short maxItem = 401;
    private readonly bool[] activeItem = new bool[maxItem];
    public override void OnCommonPacket(PacketReceiveArgs args)
    {
        if (args.Packet is IItemBase sync)
            activeItem[sync.ItemSlot] = sync.ItemType != 0;
    }

    public override void OnCleaning()
    {
        for (short i = 0; i < maxItem; ++i)
        {
            if (activeItem[i])
            {
                Parent.SendClient(new SyncItem()
                {
                    ItemSlot = i,
                    ItemType = 0
                });
                activeItem[i] = false;
            }
        }
    }
}