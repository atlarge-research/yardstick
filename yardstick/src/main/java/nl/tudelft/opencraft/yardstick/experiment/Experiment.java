package nl.tudelft.opencraft.yardstick.experiment;

import com.github.steveice10.mc.protocol.MinecraftProtocol;
import com.github.steveice10.packetlib.Client;
import com.github.steveice10.packetlib.Session;
import com.github.steveice10.packetlib.tcp.TcpSessionFactory;
import java.util.logging.Level;
import nl.tudelft.opencraft.yardstick.Options;
import nl.tudelft.opencraft.yardstick.Yardstick;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;
import nl.tudelft.opencraft.yardstick.statistic.Statistics;
import nl.tudelft.opencraft.yardstick.util.Scheduler;
import nl.tudelft.opencraft.yardstick.workload.WorkloadDumper;
import nl.tudelft.opencraft.yardstick.workload.WorkloadSessionListener;

public abstract class Experiment implements Runnable {

    public static final long TICK_MS = 50;
    //
    protected final int number;
    protected final String description;
    protected final Options options = Yardstick.OPTIONS;
    protected final SubLogger logger;

    protected long tick = 0;
    private Statistics stats;
    private WorkloadDumper dumper;

    public Experiment(int number, String desc) {
        this.number = number;
        this.description = desc;
        this.logger = GlobalLogger.getLogger().newSubLogger("Experiment " + number);
    }

    @Override
    public void run() {
        logger.info("Running: experiment " + number + " - " + description);

        for (String key : options.experimentParams.keySet()) {
            logger.info("Parameter - " + key + ": " + options.experimentParams.get(key));
        }

        if (stats != null) {
            stats.startPushing();
        }

        try {
            Scheduler sched = new Scheduler(TICK_MS);
            sched.start();
            before();
            do {
                tick();
                sched.sleepTick();
            } while (!isDone());
            after();
            logger.info("Experiment complete, exiting");
        } finally {
            try {
                dumper.close();
            } catch (Exception ex) {
                logger.log(Level.SEVERE, "Exception closing workload dumper.", ex);
            }

            if (stats != null) {
                stats.stopPushing();
            }
        }
        System.out.println("Goodbye.");
        System.exit(0);
    }

    public Statistics getStats() {
        return stats;
    }

    public void setStats(Statistics stats) {
        this.stats = stats;
    }

    public WorkloadDumper getWorkloadDumper() {
        return dumper;
    }

    public void setWorkloadDumper(WorkloadDumper dumper) {
        this.dumper = dumper;
    }

    protected Client newClient(String name) {
        Client client = new Client(options.host, options.port, new MinecraftProtocol(name), new TcpSessionFactory());
        setupClient(client, name);
        return client;
    }

    protected Bot newBot(String name) {
        Bot bot = new Bot(new MinecraftProtocol(name), options.host, options.port);
        setupClient(bot.getClient(), name);
        return bot;
    }

    private void setupClient(Client client, String name) {
        Session s = client.getSession();

        // Logger
        s.addListener(new ExperimentLogger(logger.newSubLogger(name)));

        // Statistics
        if (stats != null) {
            s.addListener(stats);
        }

        // Workload session listener
        if (dumper != null) {
            s.addListener(new WorkloadSessionListener(dumper, name));
        }
    }

    protected abstract void before();

    protected abstract void tick();

    protected abstract boolean isDone();

    protected abstract void after();

}
