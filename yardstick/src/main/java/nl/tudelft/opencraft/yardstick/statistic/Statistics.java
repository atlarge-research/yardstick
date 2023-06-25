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

package nl.tudelft.opencraft.yardstick.statistic;

import io.prometheus.client.CollectorRegistry;
import io.prometheus.client.Counter;
import io.prometheus.client.Gauge;
import io.prometheus.client.Summary;
import nl.tudelft.opencraft.yardstick.util.CountingOutputStream;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.server.ServerJoinGamePacket;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.server.ServerKeepAlivePacket;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.server.entity.ServerEntityHeadLookPacket;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.server.entity.ServerEntityMovementPacket;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.server.entity.ServerEntityTeleportPacket;
import science.atlarge.opencraft.packetlib.Session;
import science.atlarge.opencraft.packetlib.event.session.ConnectedEvent;
import science.atlarge.opencraft.packetlib.event.session.DisconnectedEvent;
import science.atlarge.opencraft.packetlib.event.session.DisconnectingEvent;
import science.atlarge.opencraft.packetlib.event.session.PacketReceivedEvent;
import science.atlarge.opencraft.packetlib.event.session.PacketSendingEvent;
import science.atlarge.opencraft.packetlib.event.session.PacketSentEvent;
import science.atlarge.opencraft.packetlib.event.session.SessionListener;
import science.atlarge.opencraft.packetlib.io.NetOutput;
import science.atlarge.opencraft.packetlib.io.stream.StreamNetOutput;
import science.atlarge.opencraft.packetlib.packet.Packet;

import java.io.IOException;
import java.util.HashSet;

/**
 * Represents a {@link SessionListener} for collecting Yardstick statistics and
 * forwarding theses to a {@link StatisticsPusher}.
 *
 * @author Admin
 */
public class Statistics implements SessionListener {

    private final Logger logger = LoggerFactory.getLogger(Statistics.class);
    private final StatisticsPusher pusher = new StatisticsPusher();
    //
    private final CountingOutputStream cos = new CountingOutputStream();
    private final NetOutput cno = new StreamNetOutput(cos);
    private final Gauge connected;
    private final Counter packIn;
    private final Counter packOut;
    private final Summary bytesIn;
    private final Summary bytesOut;
    private final Counter errors;
    private final Counter keepAliveIn;
    private final Counter entityPositionUpdate;

    private final HashSet<Session> connectedClientSessions = new HashSet<>();

    /**
     * Create a new Statistics listener.
     *
     * @param host the host of the Prometheus push gateway.
     * @param port the port of the Prometheus push gateway.
     */
    public Statistics(String host, int port) {
        this.pusher.setup(host, port);

        CollectorRegistry registry = pusher.getRegistry();
        connected = Gauge.build()
                .namespace("yardstick")
                .name("bots_connected")
                .help("Amount of isConnected bots")
                .register(registry);

        packIn = Counter.build()
                .namespace("yardstick")
                .name("packets_in")
                .help("Packets received")
                .register(registry);

        packOut = Counter.build()
                .namespace("yardstick")
                .name("packets_out")
                .help("Packets sent")
                .register(registry);

        bytesIn = Summary.build()
                .namespace("yardstick")
                .name("bytes_in")
                .help("Bytes received")
                .register(registry);

        bytesOut = Summary.build()
                .namespace("yardstick")
                .name("bytes_out")
                .help("Bytes sent")
                .register(registry);

        errors = Counter.build()
                .namespace("yardstick")
                .name("disconnect_errors")
                .help("Amount of disconnects due to errors")
                .register(registry);

        keepAliveIn = Counter.build()
                .namespace("yardstick")
                .name("keep_alive_packets_in")
                .help("The amount of Keep Alive packets received from the server.")
                .register(registry);

        entityPositionUpdate = Counter.build()
                .namespace("yardstick")
                .name("entity_position_updates")
                .help("Number of packets received that update the location or rotation of an entity.")
                .register(registry);
    }

    /**
     * Starts pushing statistics. This starts a thread which must be stopped
     * with {@link #stop()}.
     */
    public void start() {
        Thread pushThread = new Thread(pusher);
        pushThread.setName("Statistics Pusher");
        pushThread.start();
    }

    /**
     * Stops pushing statistics.
     */
    public void stop() {
        pusher.stop();
    }

    @Override
    public void packetReceived(PacketReceivedEvent pre) {
        packIn.inc();

        Packet packet = pre.getPacket();

        if (packet instanceof ServerKeepAlivePacket) {
            keepAliveIn.inc();
        } else if (packet instanceof ServerEntityMovementPacket || packet instanceof ServerEntityHeadLookPacket || packet instanceof ServerEntityTeleportPacket) {
            entityPositionUpdate.inc();
        } else if (packet instanceof ServerJoinGamePacket) {
            connectedClientSessions.add(pre.getSession());
            connected.inc();
        }

        // Count bytes
        cos.reset();
        try {
            packet.write(cno);
            cno.flush();
        } catch (IOException ex) {
            logger.error("Exception counting received packet bytes", ex);
        }

        bytesIn.observe(cos.getCount());
    }

    @Override
    public void packetSending(PacketSendingEvent packetSendingEvent) {

    }

    @Override
    public void packetSent(PacketSentEvent pse) {
        packOut.inc();

        // Count bytes
        cos.reset();
        try {
            pse.getPacket().write(cno);
            cno.flush();
        } catch (IOException ex) {
            logger.error("Exception counting sent packet bytes", ex);
        }

        bytesOut.observe(cos.getCount());
    }

    @Override
    public void connected(ConnectedEvent ce) {
        //Ignore. We increment the connections when we receive the JoinGame packet. Then we know the player is ready.
    }

    @Override
    public void disconnecting(DisconnectingEvent de) {
    }

    @Override
    public void disconnected(DisconnectedEvent de) {
        if (connectedClientSessions.remove(de.getSession())) {
            connected.dec();
        }
        if (de.getCause() != null) {
            errors.inc();
        }
    }

}
