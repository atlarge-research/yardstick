/*
 * Yardstick: A Benchmark for Minecraft-like Services
 * Copyright (C) 2020 AtLarge Research
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

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
