package nl.tudelft.opencraft.yardstick.experiment;

import org.spacehq.mc.protocol.MinecraftProtocol;
import org.spacehq.packetlib.Client;
import org.spacehq.packetlib.Session;
import org.spacehq.packetlib.tcp.TcpSessionFactory;

public class Experiment1SimpleJoin extends Experiment {

    public static final long EXPERIMENT_DURATION = 10_000;
    //
    private Client client;
    //

    public Experiment1SimpleJoin() {
        super(1,
                "A simple experiment. A bot joins the server and disconnects after 10 seconds. "
                + "The amount of packets and bytes that are both sent and received are counted and reported.");
    }

    @Override
    protected void before() {
        String name = "YSBot-1";
        client = new Client(options.host, options.port, new MinecraftProtocol(name), new TcpSessionFactory());
        Session s = client.getSession();
        s.addListener(new ExperimentLogger(logger.newSubLogger(name)));
        if (this.getStats() != null) {
            s.addListener(this.getStats());
        }
        s.connect();
    }

    @Override
    protected void tick() {
        // In this case, wait and do nothing...
    }

    @Override
    protected void after() {
        client.getSession().disconnect("disconnect");
    }

    @Override
    public boolean isDone() {
        return tick >= EXPERIMENT_DURATION || !client.getSession().isConnected();
    }

}
