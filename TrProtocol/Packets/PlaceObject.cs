namespace TrProtocol.Packets;

public class PlaceObject : Packet
{
    public override MessageID Type => MessageID.PlaceObject;
    public ShortPosition Position { get; set; }
    public short ObjectType { get; set; }
    public short Style { get; set; }
    public byte Alternate { get; set; }
    public sbyte Random { get; set; }
    public bool Direction { get; set; }
}