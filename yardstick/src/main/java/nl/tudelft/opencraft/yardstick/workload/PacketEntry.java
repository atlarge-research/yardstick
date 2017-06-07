package nl.tudelft.opencraft.yardstick.workload;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import com.github.steveice10.packetlib.packet.Packet;
import nl.tudelft.opencraft.yardstick.util.PacketUtil;

public class PacketEntry {

    private final long timestamp;
    private final String name;
    private final boolean outgoing;
    private final int length;

    public PacketEntry(long timestamp, String packet, boolean outgoing, int length) {
        this.timestamp = timestamp;
        this.name = packet;
        this.outgoing = outgoing;
        this.length = length;
    }

    public void writeTo(DataOutputStream dos) throws IOException {
        dos.writeLong(timestamp);
        dos.writeBoolean(outgoing);
        dos.writeUTF(name);
        dos.writeInt(length);
    }

    public static PacketEntry readFrom(DataInputStream dis) throws IOException {
        long timestamp = dis.readLong();
        boolean outgoing = dis.readBoolean();
        String name = dis.readUTF();
        int length = dis.readInt();
        return new PacketEntry(timestamp, name, outgoing, length);
    }

    public static PacketEntry forPacket(Packet packet, boolean outgoing) {
        long timestamp = System.currentTimeMillis();
        String packetName = packet.getClass().getSimpleName();
        int length = PacketUtil.packetLength(packet);
        return new PacketEntry(timestamp, packetName, outgoing, length);
    }

    public String toCsv() {
        StringBuilder sb = new StringBuilder();
        sb.append(timestamp).append(',');
        sb.append(outgoing).append(',');
        sb.append(name).append(',');
        sb.append(length).append('\n');
        return sb.toString();
    }

}
