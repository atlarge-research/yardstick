namespace TrProtocol.Packets;

public class ClientSyncedInventory : Packet
{
    public override MessageID Type => MessageID.ClientSyncedInventory;
}