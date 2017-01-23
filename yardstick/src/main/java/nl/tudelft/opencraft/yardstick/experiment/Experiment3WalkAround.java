package nl.tudelft.opencraft.yardstick.experiment;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.activity.WalkActivity;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;
import org.spacehq.mc.protocol.MinecraftProtocol;

import java.util.Random;

public class Experiment3WalkAround extends Experiment {

    private Random random;
    private Bot bot;
    private Vector3d originalLocation;

    public Experiment3WalkAround() {
        super(3, "A simple test demonstrating A* movement");
        this.random = new Random();
    }

    @Override
    protected void before() {
        this.bot = new Bot(new MinecraftProtocol("YSBot-1"));
        bot.getClient().getSession().addListener(stats);
        bot.connect(options.host, options.port);
        originalLocation = bot.getPlayer().getLocation();

    }

    @Override
    protected void tick() {
        if (!bot.getActivity().isActive()) {
            bot.setActivity(new WalkActivity(bot, getNewFieldLocation(originalLocation)));
        }
    }

    /**
     * Function to make bot walk in a specific area.
     *
     * @param originalLocation Original location of bot
     * @return New random location in a field that has the original location at its center.
     */
    private Vector3i getNewFieldLocation(Vector3d originalLocation) {
        int side = 100;
        int maxx = ((int) originalLocation.getX()) + side / 2;
        int minx = ((int) originalLocation.getX()) - side / 2;
        int maxz = ((int) originalLocation.getZ()) + side / 2;
        int minz = ((int) originalLocation.getZ()) - side / 2;
        int newx = random.nextInt(maxx - minx) + minx;
        int newz = random.nextInt(maxz - minz) + minz;
        return new Vector3i(newx, 0, newz);
    }

    @Override
    protected boolean isDone() {
        return false;
    }

    @Override
    protected void after() {
        bot.disconnect("disconnect");
    }
}
