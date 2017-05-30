package nl.tudelft.opencraft.yardstick.experiment;

import com.github.steveice10.mc.protocol.MinecraftProtocol;
import com.github.steveice10.packetlib.Client;
import com.github.steveice10.packetlib.Session;
import com.github.steveice10.packetlib.tcp.TcpSessionFactory;

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
        client = newClient("YSBot-1");
        client.getSession().connect();
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
