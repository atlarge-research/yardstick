namespace TrProtocol.Models;

public partial class ParticleOrchestraSettings
{
    public void Serialize(BinaryWriter writer)
    {
        writer.Write(PositionInWorld.X);
        writer.Write(PositionInWorld.Y);
        writer.Write(MovementVector.X);
        writer.Write(MovementVector.Y);
        writer.Write(PackedShaderIndex);
        writer.Write(IndexOfPlayerWhoInvokedThis);
    }

    public static ParticleOrchestraSettings DeserializeFrom(BinaryReader reader)
    {
        return new ParticleOrchestraSettings
        {
            PositionInWorld = new Vector2(reader.ReadSingle(), reader.ReadSingle()),
            MovementVector = new Vector2(reader.ReadSingle(), reader.ReadSingle()),
            PackedShaderIndex = reader.ReadInt32(),
            IndexOfPlayerWhoInvokedThis = reader.ReadByte()
        };
    }

    public Vector2 PositionInWorld;

    public Vector2 MovementVector;

    public int PackedShaderIndex;

    public byte IndexOfPlayerWhoInvokedThis;

    public const int SerializationSize = 21;
}

