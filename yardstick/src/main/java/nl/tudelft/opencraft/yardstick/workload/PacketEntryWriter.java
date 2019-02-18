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

/**
 * Represents a concurrent buffer for writing {@link PacketEntry} objects to a
 * file. The PacketEntrys are GZIPed buffered.
 */
public class PacketEntryWriter implements AutoCloseable {

    private static final SubLogger LOGGER = GlobalLogger.getLogger().newSubLogger("WorkLoadFileDumper");
    //
    private final DataOutputStream dos;
    private final Queue<PacketEntry> entries = new ConcurrentLinkedQueue<>();

    /**
     * Creates a new PacketEntryWriter.
     *
     * @param file the file to write to.
     * @throws IOException if there was an exception making a stream.
     */
    public PacketEntryWriter(File file) throws IOException {
        FileOutputStream fos = new FileOutputStream(file);
        BufferedOutputStream bos = new BufferedOutputStream(fos);
        GZIPOutputStream gos = new GZIPOutputStream(bos);
        this.dos = new DataOutputStream(gos);
    }

    /**
     * Queues a PacketEntry to be written to the file.
     *
     * @param entry the entry.
     */
    public void queue(PacketEntry entry) {
        entries.add(entry);
    }

    /**
     * Writes all PacketEntry objects to the file.
     */
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

    /**
     * Closes the writer.
     */
    @Override
    public void close() throws Exception {
        dos.flush();
        dos.close();
    }

}
