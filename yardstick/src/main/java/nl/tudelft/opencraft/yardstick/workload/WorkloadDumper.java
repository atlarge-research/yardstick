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

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import science.atlarge.opencraft.packetlib.event.session.PacketReceivedEvent;
import science.atlarge.opencraft.packetlib.event.session.PacketSentEvent;
import science.atlarge.opencraft.packetlib.packet.Packet;

import java.io.File;
import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Handles {@link PacketSentEvent}s and {@link PacketReceivedEvent}s for
 * multiple bots, writing the corresponding {@link Packet}s to a
 * {@link PacketEntryWriter} concurrently per bot.
 */
public class WorkloadDumper {

    private final Logger logger = LoggerFactory.getLogger(WorkloadDumper.class);
    private final File dumpFolder = new File("workload");
    private final Map<String, PacketEntryWriter> queues = new ConcurrentHashMap<>();
    //
    private final AtomicBoolean running = new AtomicBoolean(false);
    private Thread writerThread;

    /**
     * Creates a new WorkloadDumper.
     */
    public WorkloadDumper() {
        if (!dumpFolder.exists() && !dumpFolder.mkdirs()) {
            logger.error("Could not create folder '{}'", dumpFolder.getPath());
            throw new RuntimeException(new IOException("Could not create folder: " + dumpFolder.getPath()));
        }

        // Clear the previous dumps
        for (File file : dumpFolder.listFiles()) {
            logger.info("Deleting previous dump: " + file.getName());
            if (!file.delete()) {
                logger.warn("Could not delete file '{}'", file.getPath());
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
            logger.error("Could not create file stream: " + dumpFile.getPath(), ex);
            return null;
        }

        queues.put(botName, dumper);
        return dumper;
    }

    /**
     * Handles a PacketSentEvent for a given bot.
     *
     * @param botName the name of the bot.
     * @param pse     the event.
     */
    public void packetSent(String botName, PacketSentEvent pse) {
        handlePacket(botName, pse.getPacket(), true);
    }

    /**
     * Handles a PacketReceivedEvent for a given bot.
     *
     * @param botName the name of the bot.
     * @param pre     the event.
     */
    public void packetReceived(String botName, PacketReceivedEvent pre) {
        handlePacket(botName, pre.getPacket(), false);
    }

    /**
     * Starts the dumper thread. The thread runs as a daemon and must be stopped
     * prior to program termination by calling {@link #stop()}. The thread
     * writes all queued packets to the file every second.
     *
     * @throws IllegalStateException if the thread has already been started.
     */
    public void start() {
        if (running.getAndSet(true)) {
            throw new IllegalStateException("Write thread already started.");
        }

        writerThread = new Thread(new WriteRunnable(), "WorkloadDumper");
        writerThread.setDaemon(false);
        writerThread.start();
    }

    /**
     * Stops the dumper thread.
     *
     * @throws IllegalStateException if the thread has not been started.
     * @see #start()
     */
    public void stop() {
        if (!running.getAndSet(false)) {
            throw new IllegalStateException("Write thread not started.");
        }

        try {
            writerThread.join(2000);
        } catch (InterruptedException ex) {
            logger.error("", ex);
        }

        if (writerThread.isAlive()) {
            throw new IllegalThreadStateException("Writer thread took too long to stop");
        }

        for (PacketEntryWriter dos : queues.values()) {
            try {
                dos.close();
            } catch (Exception ex) {
                logger.error("", ex);
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

        private final Logger logger = LoggerFactory.getLogger(WriteRunnable.class);

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
                    logger.error("", ex);
                }
            }

            logger.info("Stopped write thread");
        }
    }
}
