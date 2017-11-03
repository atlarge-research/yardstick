package nl.tudelft.opencraft.yardstick.statistic;

import com.github.steveice10.mc.protocol.packet.ingame.server.ServerJoinGamePacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.ServerKeepAlivePacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityHeadLookPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityMovementPacket;
import com.github.steveice10.mc.protocol.packet.ingame.server.entity.ServerEntityTeleportPacket;
import com.github.steveice10.packetlib.Session;
import com.github.steveice10.packetlib.event.session.*;
import com.github.steveice10.packetlib.io.NetOutput;
import com.github.steveice10.packetlib.io.stream.StreamNetOutput;
import com.github.steveice10.packetlib.packet.Packet;
import io.prometheus.client.CollectorRegistry;
import io.prometheus.client.Counter;
import io.prometheus.client.Gauge;
import io.prometheus.client.Summary;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;
import nl.tudelft.opencraft.yardstick.util.CountingOutputStream;

import java.io.IOException;
import java.util.HashSet;
import java.util.logging.Level;

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

    private final HashSet<Session> connectedClientSessions = new HashSet<>();

    public Statistics(String host, int port) {
        this.logger = GlobalLogger.getLogger().newSubLogger("Statistics");
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

    public void start() {
        Thread pushThread = new Thread(pusher);
        pushThread.setName("Statistics Pusher");
        pushThread.start();
    }

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
