package nl.tudelft.opencraft.yardstick.workload;

import com.github.steveice10.packetlib.event.session.PacketReceivedEvent;
import com.github.steveice10.packetlib.event.session.PacketSentEvent;
import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.logging.Level;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;

public class WorkloadDumper implements AutoCloseable {

    private static final SubLogger LOGGER = GlobalLogger.getLogger().newSubLogger("WorkloadDumper");
    private final File dumpFolder = new File("workload");
    private final Map<String, FilePacketDumper> dumpers = new HashMap<>();
    //

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

    private FilePacketDumper getDumper(String botName) {
        FilePacketDumper dumper = dumpers.get(botName);

        if (dumper != null) {
            return dumper;
        }

        File dumpFile = new File(dumpFolder, botName + ".bin");

        try {
            dumper = new FilePacketDumper(dumpFile);
        } catch (IOException ex) {
            LOGGER.log(Level.SEVERE, "Could not create file stream: " + dumpFile.getPath(), ex);
            return null;
        }

        dumpers.put(botName, dumper);

        return dumper;
    }

    public void packetSent(String botName, PacketSentEvent pse) {
        FilePacketDumper dumper = getDumper(botName);

        if (dumper == null) {
            return;
        }

        try {
            dumper.dump(pse.getPacket(), true);
        } catch (Exception ex) {
            LOGGER.log(Level.SEVERE, "Could not write packet for: " + botName, ex);
        }
    }

    public void packetReceived(String botName, PacketReceivedEvent pre) {
        FilePacketDumper dumper = getDumper(botName);

        if (dumper == null) {
            return;
        }

        try {
            dumper.dump(pre.getPacket(), false);
        } catch (Exception ex) {
            LOGGER.log(Level.SEVERE, "Could not write packet for: " + botName, ex);
        }
    }

    @Override
    public void close() throws Exception {
        for (FilePacketDumper dos : dumpers.values()) {
            dos.close();
        }

        dumpers.clear();
    }

}
