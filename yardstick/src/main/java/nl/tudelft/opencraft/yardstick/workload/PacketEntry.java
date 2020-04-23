package nl.tudelft.opencraft.yardstick.workload;

import com.github.steveice10.packetlib.io.buffer.ByteBufferNetOutput;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import com.github.steveice10.packetlib.packet.Packet;

import java.nio.BufferOverflowException;
import java.nio.ByteBuffer;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;
import nl.tudelft.opencraft.yardstick.util.PacketUtil;

/**
 * Represents a snapshot of information of a specific message between the
 * Minecraft server and client.
 */
public class PacketEntry {

    private static final SubLogger LOGGER = GlobalLogger.getLogger().newSubLogger("PacketEntry");
    private final long timestamp;
    private final String name;
    private final boolean outgoing;
    private final int length;
    private final byte[] payload;

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
        this.payload = null;
    }

    public PacketEntry(long timestamp, String packet, boolean outgoing, int length, byte[] payload) {
        this.timestamp = timestamp;
        this.name = packet;
        this.outgoing = outgoing;
        this.length = length;
        this.payload = payload;
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
        dos.writeInt(payload != null ? payload.length : 0);
        if (payload != null) {
            dos.write(payload);
        }
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
        int payloadlength = dis.readInt();
        byte[] payload = dis.readNBytes(payloadlength);
        return new PacketEntry(timestamp, name, outgoing, length, payload);
    }

    /**
     * Converts a {@link Packet} to a PacketEntry.
     *
     * @param packet the packet.
     * @param outgoing whether the packet was client->server.
     * @return the PacketEntry.
     */
    public static PacketEntry forPacket(Packet packet, boolean outgoing, boolean dumpPacketContents) {
        long timestamp = System.currentTimeMillis();
        String packetName = packet.getClass().getSimpleName();
        int length = PacketUtil.packetLength(packet);
        byte[] array = null;
        if (dumpPacketContents) {
            ByteBuffer buffer = ByteBuffer.allocate(length);
            ByteBufferNetOutput output = new ByteBufferNetOutput(buffer);
            try {
                packet.write(output);
                array = buffer.array();
            } catch (IOException e) {
                LOGGER.warning(String.format("Could not dump contents of packet with name %s", packetName));
            } catch (BufferOverflowException a) {
                LOGGER.warning("overflow length:" + length + " packet size: ");
            }
        }
        return new PacketEntry(timestamp, packetName, outgoing, length, array);
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
        sb.append(length).append(',');
        String payloadInHex = bytesToHex(payload);
        sb.append(payloadInHex.length()).append(",");
        sb.append(payloadInHex).append('\n');
        return sb.toString();
    }

    // https://www.mkyong.com/java/java-how-to-convert-bytes-to-hex/
    private String bytesToHex(byte[] hashInBytes) {
        if (hashInBytes == null) {
            return "";
        }
        StringBuilder sb = new StringBuilder();
        for (byte b : hashInBytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }

}
