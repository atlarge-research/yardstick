package nl.tudelft.opencraft.yardstick.workload;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import science.atlarge.opencraft.packetlib.packet.Packet;
import nl.tudelft.opencraft.yardstick.util.PacketUtil;

/**
 * Represents a snapshot of information of a specific message between the
 * Minecraft server and client.
 */
public class PacketEntry {

    private final long timestamp;
    private final String name;
    private final boolean outgoing;
    private final int length;

    /**
     * Creates a new PacketEntry.
     *
     * @param timestamp the unix nanotime that the message was sent or did
     * arrive.
     * @param packet a shorthand name for the message type.
     * @param outgoing true if the message was client->server, false otherwise.
     * @param length the length of the message in bytes.
     */
    public PacketEntry(long timestamp, String packet, boolean outgoing, int length) {
        this.timestamp = timestamp;
        this.name = packet;
        this.outgoing = outgoing;
        this.length = length;
    }

    /**
     * Writes the message to a DataOutputStream.
     *
     * @param dos the stream.
     * @throws IOException if the DOS throws an exception.
     */
    public void writeTo(DataOutputStream dos) throws IOException {
        dos.writeLong(timestamp);
        dos.writeBoolean(outgoing);
        dos.writeUTF(name);
        dos.writeInt(length);
    }

    /**
     * Reads a message from a DataInputStream.
     *
     * @param dis the stream.
     * @return the message read.
     * @throws IOException if the DOS throws an exception.
     */
    public static PacketEntry readFrom(DataInputStream dis) throws IOException {
        long timestamp = dis.readLong();
        boolean outgoing = dis.readBoolean();
        String name = dis.readUTF();
        int length = dis.readInt();
        return new PacketEntry(timestamp, name, outgoing, length);
    }

    /**
     * Converts a {@link Packet} to a PacketEntry.
     *
     * @param packet the packet.
     * @param outgoing whether the packet was client->server.
     * @return the PacketEntry.
     */
    public static PacketEntry forPacket(Packet packet, boolean outgoing) {
        long timestamp = System.currentTimeMillis();
        String packetName = packet.getClass().getSimpleName();
        int length = PacketUtil.packetLength(packet);
        return new PacketEntry(timestamp, packetName, outgoing, length);
    }

    /**
     * Converts the PacketEntry to a CSV String with one entry, ending in a
     * newline character.
     *
     * @return The CSV string.
     */
    public String toCsv() {
        StringBuilder sb = new StringBuilder();
        sb.append(timestamp).append(',');
        sb.append(outgoing).append(',');
        sb.append(name).append(',');
        sb.append(length).append('\n');
        return sb.toString();
    }

}
