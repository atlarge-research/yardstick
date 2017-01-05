package nl.tudelft.opencraft.yardstick.experiment;

import java.io.IOException;
import java.util.logging.Level;
import nl.tudelft.opencraft.yardstick.Options;
import nl.tudelft.opencraft.yardstick.Report;
import nl.tudelft.opencraft.yardstick.util.CountingOutputStream;
import org.spacehq.mc.protocol.MinecraftProtocol;
import org.spacehq.packetlib.Client;
import org.spacehq.packetlib.event.session.ConnectedEvent;
import org.spacehq.packetlib.event.session.DisconnectedEvent;
import org.spacehq.packetlib.event.session.DisconnectingEvent;
import org.spacehq.packetlib.event.session.PacketReceivedEvent;
import org.spacehq.packetlib.event.session.PacketSentEvent;
import org.spacehq.packetlib.event.session.SessionListener;
import org.spacehq.packetlib.io.NetOutput;
import org.spacehq.packetlib.io.stream.StreamNetOutput;
import org.spacehq.packetlib.tcp.TcpSessionFactory;

public class Experiment1SimpleJoin extends Experiment implements SessionListener {

    public static final long EXPERIMENT_DURATION = 10_000;
    //
    private Client client;
    //
    private final CountingOutputStream cos = new CountingOutputStream();
    private final NetOutput cno = new StreamNetOutput(cos);
    private int packIn = 0;
    private int packOut = 0;
    private long bytesIn;
    private long bytesOut;

    public Experiment1SimpleJoin(Options opts) {
        super(1,
                "A simple experiment. A bot joins the server and disconnects after 10 seconds. "
                + "The amount of packets and bytes that are both sent and received are counted and reported.",
                opts);
    }

    @Override
    protected void before() {
        client = new Client(options.host, options.port, new MinecraftProtocol("YSBot-1"), new TcpSessionFactory());
        client.getSession().addListener(this);
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
    public Report report() {
        Report r = new Report("Simple Join");
        r.put("packets_in", "Packets received", packIn);
        r.put("bytes_in", "Bytes received", bytesIn);
        r.put("bytes_per_sec_in", "Bytes/sec received", bytesIn / (EXPERIMENT_DURATION / 1000));
        r.put("packets_out", "Packets sent", packOut);
        r.put("bytes_out", "Bytes sent", bytesOut);
        r.put("bytes_per_sec_out", "Bytes/sec sent", bytesOut / (EXPERIMENT_DURATION / 1000));
        r.seal();

        return r;
    }

    @Override
    public boolean isDone() {
        return tick >= EXPERIMENT_DURATION || !client.getSession().isConnected();
    }

    @Override
    public void packetReceived(PacketReceivedEvent pre) {
        //logger.info("Packet received: " + pre.getPacket().getClass().getSimpleName());
        packIn++;

        // Count bytes
        cos.reset();
        try {
            pre.getPacket().write(cno);
            cno.flush();
        } catch (IOException ex) {
            throw new RuntimeException(ex);
        }

        bytesIn += cos.getCount();
    }

    @Override
    public void packetSent(PacketSentEvent pse) {
        //logger.info("Packet sent: " + pse.getPacket().getClass().getSimpleName());
        packOut++;

        // Count bytes
        cos.reset();
        try {
            pse.getPacket().write(cno);
            cno.flush();
        } catch (IOException ex) {
            throw new RuntimeException(ex);
        }

        bytesOut += cos.getCount();
    }

    @Override
    public void connected(ConnectedEvent ce) {
        logger.info("Connected!");
    }

    @Override
    public void disconnecting(DisconnectingEvent de) {
        logger.info("Disconnecting");
    }

    @Override
    public void disconnected(DisconnectedEvent de) {
        logger.info("Disconnected: " + de.getReason());
        if (de.getCause() != null) {
            logger.log(Level.SEVERE, "Connection closed unexpectedly!", de.getCause());
        }
    }

}
