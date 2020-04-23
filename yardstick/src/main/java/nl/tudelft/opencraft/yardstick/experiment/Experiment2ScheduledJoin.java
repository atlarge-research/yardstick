package nl.tudelft.opencraft.yardstick.experiment;

import java.util.ArrayList;
import java.util.List;
import com.github.steveice10.packetlib.Client;

public class Experiment2ScheduledJoin extends Experiment {

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

    public Experiment2ScheduledJoin() {
        super(2, "Gradually lets bots join a server in a scheduled manner. Supports a clustered approach.");
    }

    @Override
    protected void before() {
        // Quick and dirty. TODO: Error handling
        this.nodeId = Integer.parseInt(options.experimentParams.getOrDefault("id", "2"));
        this.nodeCount = Integer.parseInt(options.experimentParams.getOrDefault("nodes", "2"));
        this.botsTotal = Integer.parseInt(options.experimentParams.getOrDefault("bots", "2"));
        this.interval = Integer.parseInt(options.experimentParams.getOrDefault("interval", "1"));
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
 /*
        if (nodeId != node) {
            logger.info("Bot " + botsJoined + " joining on node " + node);
            logger.info("kekw");
            return;
        }
*/
        logger.info("Bot " + botsJoined + " joining on node " + node + " (this node)");

        // Connect
        Client client = newClient("YSBot-" + node + "-" + botsJoined);
        client.getSession().connect();

        if (!client.getSession().isConnected()) {
            logger.info("Terminating...");
            botsJoined = Integer.MAX_VALUE;
        }

        if (step == botsTotal) {
            logger.info("All bots have joined. Sleeping 10 seconds");
        }
    }

    @Override
    protected void after() {
        for (Client client : clients) {
            client.getSession().disconnect("disconnect");
        }
        clients.clear();
    }

}
