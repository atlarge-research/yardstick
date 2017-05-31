package nl.tudelft.opencraft.yardstick.workload;

import java.io.BufferedOutputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.logging.Level;
import com.github.steveice10.packetlib.Session;
import com.github.steveice10.packetlib.event.session.PacketReceivedEvent;
import com.github.steveice10.packetlib.event.session.PacketSentEvent;
import com.github.steveice10.packetlib.io.NetOutput;
import com.github.steveice10.packetlib.io.stream.StreamNetOutput;
import com.github.steveice10.packetlib.packet.Packet;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;
import nl.tudelft.opencraft.yardstick.util.CountingOutputStream;
import nl.tudelft.opencraft.yardstick.util.PacketUtil;

public class WorkloadDumper implements AutoCloseable {

    private static final SubLogger LOGGER = GlobalLogger.getLogger().newSubLogger("WorkloadDumper");
    private final File dumpFolder = new File("workload");
    private final Map<String, DataOutputStream> writers = new HashMap<>();
    //
    private final CountingOutputStream cos = new CountingOutputStream();
    private final NetOutput cno = new StreamNetOutput(cos);

    public WorkloadDumper() {
        if (!dumpFolder.exists() && !dumpFolder.mkdirs()) {
            LOGGER.severe("Could not create folder: " + dumpFolder.getPath());
            throw new RuntimeException(new IOException("Could not create folder: " + dumpFolder.getPath()));
        }

        // Clear the previous dumps
        for (File file : dumpFolder.listFiles()) {
            LOGGER.info("Deleting previous dump: " + file.getName());
            if (!file.delete()) {
                LOGGER.warning("Could not delete file: " + file.getPath());
            }
        }
    }

    private DataOutputStream createDos(String botName) {
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
        } catch (Exception ex) {
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
        } catch (Exception ex) {
            LOGGER.log(Level.SEVERE, "Could not write packet for: " + botName, ex);
        }
    }

    private void serializeWrite(Packet pack, Session session, DataOutputStream dos, boolean outgoing) throws Exception {
        cos.reset();
        pack.write(cno);
        long length = cos.getCount();

        int packId = PacketUtil.getPacketId(session.getPacketProtocol(), pack, outgoing);

        // Write the data to the dump
        dos.writeLong(System.currentTimeMillis());
        dos.writeByte(outgoing ? 1 : 2);
        //dos.writeInt(packId);
        dos.writeUTF(pack.getClass().getSimpleName());
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
