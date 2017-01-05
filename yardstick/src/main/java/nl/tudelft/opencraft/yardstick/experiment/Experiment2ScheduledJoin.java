package nl.tudelft.opencraft.yardstick.experiment;

import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import nl.tudelft.opencraft.yardstick.Options;
import nl.tudelft.opencraft.yardstick.Report;
import org.spacehq.mc.protocol.MinecraftProtocol;
import org.spacehq.packetlib.Client;
import org.spacehq.packetlib.event.session.ConnectedEvent;
import org.spacehq.packetlib.event.session.DisconnectedEvent;
import org.spacehq.packetlib.event.session.DisconnectingEvent;
import org.spacehq.packetlib.event.session.PacketReceivedEvent;
import org.spacehq.packetlib.event.session.PacketSentEvent;
import org.spacehq.packetlib.event.session.SessionListener;
import org.spacehq.packetlib.tcp.TcpSessionFactory;

public class Experiment2ScheduledJoin extends Experiment implements SessionListener {

    // Index of the current app instance
    private int nodeId;

    // Amount of app instances
    private int nodeCount;

    // Total amount of bots to let the app instances join the server combined
    private int botsTotal;

    // Interval between joins, in milliseconds
    private int interval;

    // The amount of bots that have joined
    private int botsJoined = 0;

    // All connections
    private final List<Client> clients = new ArrayList<>();

    public Experiment2ScheduledJoin(Options opts) {
        super(2, "Gradually lets bots join a server in a scheduled manner. Supports a clustered approach.", opts);
    }

    @Override
    protected void before() {
        // Quick and dirty. TODO: Error handling
        this.nodeId = Integer.parseInt(options.experimentParams.get("id"));
        this.nodeCount = Integer.parseInt(options.experimentParams.get("nodes"));
        this.botsTotal = Integer.parseInt(options.experimentParams.get("bots"));
        this.interval = Integer.parseInt(options.experimentParams.get("interval"));
    }

    @Override
    protected boolean isDone() {
        // Special value
        if (botsJoined == Integer.MAX_VALUE) {
            return true;
        }

        return tick > botsTotal * interval + 10_000;
    }

    @Override
    protected void tick() {
        // Calculate which bot should be joining on this tick
        int step = (int) Math.floorDiv(tick, interval) + 1;

        // If the bot has already joined, or all bots have joined
        if (step <= botsJoined || step > botsTotal) {
            return; // No action
        }

        // Calculate on which machine this bot should join
        int node = botsJoined % nodeCount;
        botsJoined++; // Presume the bot will join

        if (nodeId != node) {
            System.out.println("Bot " + botsJoined + " joining on node " + node);
            return;
        }

        System.out.println("Bot " + botsJoined + " joining on node " + node + " (this node)");

        // Connect
        Client client = new Client(options.host, options.port, new MinecraftProtocol("YSBot-" + node + "-" + botsJoined), new TcpSessionFactory());
        client.getSession().addListener(this);
        client.getSession().connect();

        if (client.getSession().isConnected()) {
            System.out.println("  > Connected");
        } else {
            System.out.println("Terminating...");
            botsJoined = Integer.MAX_VALUE;
        }

        if (step == botsTotal) {
            System.out.println("All bots have joined. Sleeping 10 seconds");
        }
    }

    @Override
    protected void after() {
        for (Client client : clients) {
            client.getSession().disconnect("disconnect");
        }
        clients.clear();
    }

    @Override
    public Report report() {
        Report r = new Report("Scheduled Join");

        r.put("node_id", "Node ID", nodeId);
        r.put("node_count", "Node count", nodeCount);
        r.put("bots_joined", "Bots joined", botsJoined);
        r.put("interval", "Interval (ms)", interval);

        r.seal();
        return r;
    }

    @Override
    public void packetReceived(PacketReceivedEvent pre) {
    }

    @Override
    public void packetSent(PacketSentEvent pse) {
    }

    @Override
    public void connected(ConnectedEvent ce) {
    }

    @Override
    public void disconnecting(DisconnectingEvent de) {
    }

    @Override
    public void disconnected(DisconnectedEvent de) {
        if (de.getCause() != null) {
            logger.log(Level.SEVERE, "Connection closed unexpectedly!", de.getCause());
        }
    }

}
