package nl.tudelft.opencraft.yardstick.experiment;

import com.github.steveice10.mc.auth.exception.request.RequestException;
import com.github.steveice10.packetlib.Client;
import nl.tudelft.opencraft.yardstick.bot.Bot;

public class Experiment8 extends Experiment {

    public static final long EXPERIMENT_DURATION = 10000;
    //
    private Client client;
    private Bot bot;
    private boolean done = false;
    //

    public Experiment8() {
        super(8,
                "A simple experiment. A bot joins the server and disconnects after 10 seconds. "
                        + "The amount of packets and bytes that are both sent and received are counted and reported.");
    }

    @Override
    protected void before() {

        try {
            this.bot = newBot("YSBot-1");
        } catch (RequestException e) {
            logger.severe("Could not connect bot. Stopping experiment.");
            this.done = true;
            return;
        }
        this.bot.connect();
    }
        /*
        client = newClient("YSBot-1");
        client.getSession().connect();
    }
*/
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
        return done;// || !client.getSession().isConnected();
    }

}
