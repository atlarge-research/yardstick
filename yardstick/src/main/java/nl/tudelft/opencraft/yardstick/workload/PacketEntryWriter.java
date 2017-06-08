package nl.tudelft.opencraft.yardstick.workload;

import java.io.BufferedOutputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.Queue;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.logging.Level;
import java.util.zip.GZIPOutputStream;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;

public class PacketEntryWriter implements AutoCloseable {

    private static final SubLogger LOGGER = GlobalLogger.getLogger().newSubLogger("WorkLoadFileDumper");
    //
    private final DataOutputStream dos;
    private final Queue<PacketEntry> entries = new ConcurrentLinkedQueue<>();

    public PacketEntryWriter(File file) throws IOException {
        FileOutputStream fos = new FileOutputStream(file);
        BufferedOutputStream bos = new BufferedOutputStream(fos);
        GZIPOutputStream gos = new GZIPOutputStream(bos);
        this.dos = new DataOutputStream(gos);
    }

    public void queue(PacketEntry entry) {
        entries.add(entry);
    }

    public void writeQueued() {
        while (!entries.isEmpty()) {
            PacketEntry entry = entries.poll();
            try {
                entry.writeTo(dos);
            } catch (IOException ex) {
                LOGGER.log(Level.SEVERE, "Could not write packet: " + entry.toCsv(), ex);
            }
        }
    }

    @Override
    public void close() throws Exception {
        dos.flush();
        dos.close();
    }

}
