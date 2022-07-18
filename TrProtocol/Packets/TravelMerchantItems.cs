namespace TrProtocol.Packets;

public class TravelMerchantItems : Packet
{
    public override MessageID Type => MessageID.TravelMerchantItems;
    [ArraySize(40)] public short[] ShopItems { get; set; }
}