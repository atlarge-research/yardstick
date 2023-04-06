namespace Dimensions.Core;

public abstract class ClientHandler
{
    protected Client Parent { get; private set; }

    public ClientHandler SetParent(Client client)
    {
        Parent = client;
        return this;
    }

    public virtual void OnCommonPacket(PacketReceiveArgs args)
    {
    }
    public virtual void OnS2CPacket(PacketReceiveArgs args)
    {
    }
    public virtual void OnC2SPacket(PacketReceiveArgs args)
    {
    }
    public virtual void OnCleaning()
    {
    }
}