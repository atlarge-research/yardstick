package nl.tudelft.opencraft.yardstick.workload;

import com.github.steveice10.mc.protocol.MinecraftProtocol;
import com.github.steveice10.packetlib.Session;
import com.github.steveice10.packetlib.event.session.PacketReceivedEvent;
import com.github.steveice10.packetlib.event.session.PacketSentEvent;
import com.github.steveice10.packetlib.io.NetOutput;
import com.github.steveice10.packetlib.io.stream.StreamNetInput;
import com.github.steveice10.packetlib.io.stream.StreamNetOutput;
import com.github.steveice10.packetlib.packet.Packet;
import com.github.steveice10.packetlib.packet.PacketHeader;
import com.github.steveice10.packetlib.tcp.io.ByteBufNetInput;
import com.github.steveice10.packetlib.tcp.io.ByteBufNetOutput;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.Unpooled;
import java.io.BufferedOutputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.logging.Level;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;
import nl.tudelft.opencraft.yardstick.util.CountingOutputStream;

public class WorkloadDumper implements AutoCloseable {

    private static final SubLogger LOGGER = GlobalLogger.getLogger().newSubLogger("WorkloadDumper");
    private final File dumpFolder = new File("workload");
    private final Map<String, DataOutputStream> writers = new HashMap<>();
    //
    private final CountingOutputStream cos = new CountingOutputStream();
    private final NetOutput cno = new StreamNetOutput(cos);

    private DataOutputStream createDos(String botName) {
        if (dumpFolder.exists()) {
            // Clear the previous dumps
            for (File file : dumpFolder.listFiles()) {
                if (!file.delete()) {
                    LOGGER.warning("Could not delete file: " + file.getPath());
                }
            }

        } else {
            // Create the workload folder
            if (!dumpFolder.mkdirs()) {
                LOGGER.severe("Could not create folder: " + dumpFolder.getPath());
                return null;
            }
        }

        File dumpFile = new File(dumpFolder, botName + ".bin");
        try {
            return new DataOutputStream(new BufferedOutputStream(new FileOutputStream(dumpFile)));
        } catch (IOException ex) {
            LOGGER.log(Level.SEVERE, "Could not create file stream: " + dumpFile.getPath(), ex);
            return null;
        }
    }

    private DataOutputStream getDos(String botName) {
        DataOutputStream dos = writers.get(botName);

        if (dos == null) {
            dos = createDos(botName);

            if (dos == null) {
                return null;
            }

            writers.put(botName, dos);
        }

        return dos;
    }

    public void packetSent(String botName, PacketSentEvent pse) {
        DataOutputStream dos = getDos(botName);

        if (dos == null) {
            return;
        }

        try {
            serializeWrite(pse.getPacket(), pse.getSession(), dos, true);
        } catch (IOException ex) {
            LOGGER.log(Level.SEVERE, "Could not write packet for: " + botName, ex);
        }
    }

    public void packetReceived(String botName, PacketReceivedEvent pre) {
        DataOutputStream dos = getDos(botName);

        if (dos == null) {
            return;
        }

        try {
            serializeWrite(pre.getPacket(), pre.getSession(), dos, false);
        } catch (IOException ex) {
            LOGGER.log(Level.SEVERE, "Could not write packet for: " + botName, ex);
        }
    }

    private void serializeWrite(Packet pack, Session session, DataOutputStream dos, boolean sent) throws IOException {
        if (sent)
        
        // Read the packet length
        cos.reset();
        pack.write(cno);
        long length = cos.getCount();

        // Hack to read the packet ID
        MinecraftProtocol prot = (MinecraftProtocol) session.getPacketProtocol();
        PacketHeader ph = prot.getPacketHeader();

        ByteBuf buf = Unpooled.buffer((int) length);
        ByteBufNetOutput bufOut = new ByteBufNetOutput(buf);

        pack.write(bufOut);
        bufOut.flush();
        LOGGER.info("Packet: " + buf.readableBytes() + " " + pack.getClass().getSimpleName());

        ByteBufNetInput bufIn = new ByteBufNetInput(buf);
        ph.readLength(bufIn, buf.readableBytes());
        int packId = prot.getPacketHeader().readPacketId(bufIn);

        buf.release();

        // Write the data to the dump
        dos.writeLong(System.currentTimeMillis());
        dos.writeByte(sent ? 1 : 2);
        dos.writeInt(packId);
        dos.writeLong(length);
    }

    @Override
    public void close() throws Exception {
        for (DataOutputStream dos : writers.values()) {
            dos.flush();
            dos.close();
        }

        writers.clear();
    }

}
