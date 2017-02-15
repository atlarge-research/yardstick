package nl.tudelft.opencraft.yardstick.statistic;

import java.io.IOException;
import java.util.logging.Level;
import io.prometheus.client.CollectorRegistry;
import io.prometheus.client.Counter;
import io.prometheus.client.Gauge;
import io.prometheus.client.Summary;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;
import org.spacehq.mc.protocol.packet.ingame.server.ServerKeepAlivePacket;
import org.spacehq.mc.protocol.packet.ingame.server.entity.*;
import org.spacehq.packetlib.event.session.ConnectedEvent;
import org.spacehq.packetlib.event.session.DisconnectedEvent;
import org.spacehq.packetlib.event.session.DisconnectingEvent;
import org.spacehq.packetlib.event.session.PacketReceivedEvent;
import org.spacehq.packetlib.event.session.PacketSentEvent;
import org.spacehq.packetlib.event.session.SessionListener;
import org.spacehq.packetlib.io.NetOutput;
import org.spacehq.packetlib.io.stream.StreamNetOutput;
import org.spacehq.packetlib.packet.Packet;

public class Statistics implements SessionListener {

    private final SubLogger logger;
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

    public Statistics(String host, int port) {
        this.logger = GlobalLogger.getLogger().newSubLogger("Statistics");
        this.pusher.setup(host, port);

        CollectorRegistry registry = pusher.getRegistry();
        connected = Gauge.build()
                .namespace("yardstick")
                .name("bots_connected")
                .help("Amount of connected bots")
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

    public void startPushing() {
        Thread pushThread = new Thread(pusher);
        pushThread.setName("Statistics Pusher");
        pushThread.start();
    }

    public void stopPushing() {
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
        }

        // Count bytes
        cos.reset();
        try {
            packet.write(cno);
            cno.flush();
        } catch (IOException ex) {
            logger.log(Level.SEVERE, "Exception counting received packet bytes", ex);
        }

        bytesIn.observe(cos.getCount());
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
            logger.log(Level.SEVERE, "Exception counting sent packet bytes", ex);
        }

        bytesOut.observe(cos.getCount());
    }

    @Override
    public void connected(ConnectedEvent ce) {
        connected.inc();
    }

    @Override
    public void disconnecting(DisconnectingEvent de) {
    }

    @Override
    public void disconnected(DisconnectedEvent de) {
        connected.dec();
        if (de.getCause() != null) {
            errors.inc();
        }
    }

}
