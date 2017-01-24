package nl.tudelft.opencraft.yardstick.experiment;

import java.util.Random;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.Task;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTask;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;
import org.spacehq.mc.protocol.MinecraftProtocol;

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
        this.bot.connect(options.host, options.port);
        if (this.getStats() != null) {
            this.bot.getClient().getSession().addListener(this.getStats());
        }
        while (this.bot.getPlayer() == null) {
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                e.printStackTrace();
                return;
            }
        }
        this.originalLocation = this.bot.getPlayer().getLocation();
    }

    @Override
    protected void tick() {
        Task t = bot.getTask();
        if (t == null || t.getStatus().getType() != TaskStatus.StatusType.IN_PROGRESS) {
            bot.setTask(new WalkTask(bot, getNewFieldLocation(originalLocation)));
        }
    }

    /**
     * Function to make bot walk in a specific area.
     *
     * @param originalLocation Original location of bot
     * @return New random location in a field that has the original location at
     * its center.
     */
    private Vector3i getNewFieldLocation(Vector3d originalLocation) {
        int side = 100;
        int maxx = ((int) originalLocation.getX()) + side / 2;
        int minx = ((int) originalLocation.getX()) - side / 2;
        int maxz = ((int) originalLocation.getZ()) + side / 2;
        int minz = ((int) originalLocation.getZ()) - side / 2;
        int newx = random.nextInt(maxx - minx) + minx;
        int newz = random.nextInt(maxz - minz) + minz;
        return new Vector3i(newx, ((int) this.originalLocation.getY()), newz);
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
