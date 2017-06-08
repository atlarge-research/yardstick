package nl.tudelft.opencraft.yardstick.workload;

import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.logging.Level;
import com.github.steveice10.packetlib.event.session.PacketReceivedEvent;
import com.github.steveice10.packetlib.event.session.PacketSentEvent;
import com.github.steveice10.packetlib.packet.Packet;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;

public class WorkloadDumper {

    private static final SubLogger LOGGER = GlobalLogger.getLogger().newSubLogger("WorkloadDumper");
    private final File dumpFolder = new File("workload");
    private final Map<String, PacketEntryWriter> queues = new HashMap<>();
    //
    private final AtomicBoolean running = new AtomicBoolean(false);
    private Thread writerThread;

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

    private PacketEntryWriter getQueue(String botName) {
        PacketEntryWriter dumper = queues.get(botName);

        if (dumper != null) {
            return dumper;
        }

        File dumpFile = new File(dumpFolder, botName + ".bin");

        try {
            dumper = new PacketEntryWriter(dumpFile);
        } catch (IOException ex) {
            LOGGER.log(Level.SEVERE, "Could not create file stream: " + dumpFile.getPath(), ex);
            return null;
        }

        queues.put(botName, dumper);
        return dumper;
    }

    public void packetSent(String botName, PacketSentEvent pse) {
        handlePacket(botName, pse.getPacket(), true);
    }

    public void packetReceived(String botName, PacketReceivedEvent pre) {
        handlePacket(botName, pre.getPacket(), false);
    }

    public void start() {
        if (running.getAndSet(true)) {
            throw new IllegalStateException("Write thread already started.");
        }

        writerThread = new Thread(new WriteRunnable(), "WorkloadDumper");
        writerThread.setDaemon(false);
        writerThread.start();
    }

    public void stop() {
        if (!running.getAndSet(false)) {
            throw new IllegalStateException("Write thread not started.");
        }

        try {
            writerThread.join(2000);
        } catch (InterruptedException ex) {
            LOGGER.log(Level.SEVERE, null, ex);
        }

        if (writerThread.isAlive()) {
            throw new IllegalThreadStateException("Writer thread took too long to stop");
        }

        for (PacketEntryWriter dos : queues.values()) {
            try {
                dos.close();
            } catch (Exception ex) {
                LOGGER.log(Level.SEVERE, null, ex);
            }
        }

        queues.clear();
    }

    private void handlePacket(String botName, Packet packet, boolean outgoing) {
        PacketEntryWriter dumper = getQueue(botName);

        if (dumper == null) {
            return;
        }

        dumper.queue(PacketEntry.forPacket(packet, outgoing));
    }

    private class WriteRunnable implements Runnable {

        private final SubLogger logger = WorkloadDumper.LOGGER.newSubLogger("WriteThread");

        @Override
        public void run() {
            running.set(true);
            logger.info("Started write thread");

            while (running.get()) {
                for (PacketEntryWriter peq : queues.values()) {
                    peq.writeQueued();
                }

                try {
                    Thread.sleep(1000);
                } catch (InterruptedException ex) {
                    logger.log(Level.SEVERE, null, ex);
                }
            }

            logger.info("Stopped write thread");
        }
    }
}
