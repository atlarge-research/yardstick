namespace TrProtocol.Models;

[Serializer(typeof(PrimitiveFieldSerializer<PylonPacketType>))]
public enum PylonPacketType : byte
{
    PylonWasAdded,
    PylonWasRemoved,
    PlayerRequestsTeleport
}
