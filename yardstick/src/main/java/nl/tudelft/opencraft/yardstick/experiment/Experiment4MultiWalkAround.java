package nl.tudelft.opencraft.yardstick.experiment;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.Task;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTask;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;
import org.spacehq.mc.protocol.MinecraftProtocol;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.UUID;

public class Experiment4MultiWalkAround extends Experiment {

    private Random random;
    private List<Bot> botList;

    public Experiment4MultiWalkAround() {
        super(3, "A simple test demonstrating A* movement");
        this.random = new Random();
        this.botList = new ArrayList<>();
    }

    @Override
    protected void before() {
        for (int i = 0; i < 100; i++) {
            botList.add(createBot());
        }
    }

    @Override
    protected void tick() {
        for (Bot bot : botList) {
            botTick(bot);
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
        int side = 64;
        int maxx = ((int) originalLocation.getX()) + side / 2;
        int minx = ((int) originalLocation.getX()) - side / 2;
        int maxz = ((int) originalLocation.getZ()) + side / 2;
        int minz = ((int) originalLocation.getZ()) - side / 2;
        int newx = random.nextInt(maxx - minx) + minx;
        int newz = random.nextInt(maxz - minz) + minz;
        return new Vector3i(newx, 4, newz);
    }

    private Vector3i getNewLongDistanceTarget(Vector3d originalLocation) {
        int maxDist = 64 * 5;
        int minDist = 64 * 1;
        int distance = random.nextInt(maxDist - minDist) + minDist;
        int angle = random.nextInt(360);
        int newX = (int) (originalLocation.getX() + (distance * Math.cos(angle)));
        int newZ = (int) (originalLocation.getZ() + (distance * Math.sin(angle)));
        return new Vector3i(newX, 4, newZ);
    }

    private void botTick(Bot bot) {
        Task t = bot.getTask();
        if (t == null || t.getStatus().getType() != TaskStatus.StatusType.IN_PROGRESS) {
            Vector3i newLocation;
            if (random.nextDouble() < 0.1) {
                newLocation = getNewLongDistanceTarget(bot.getPlayer().getLocation());
            } else {
                newLocation = getNewFieldLocation(bot.getPlayer().getLocation());
            }
            logger.info(String.format("Setting task for bot to walk to %s", newLocation));
            bot.setTask(new WalkTask(bot, newLocation));
        }
    }

    private Bot createBot() {
        Bot bot = new Bot(new MinecraftProtocol(UUID.randomUUID().toString().substring(0, 6)));
        bot.connect(options.host, options.port);
        if (this.getStats() != null) {
            bot.getClient().getSession().addListener(this.getStats());
        }
        while (bot.getPlayer() == null || bot.getPlayer().getLocation() == null) {
            if (!bot.getClient().getSession().isConnected()) {
                return null;
            }
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                e.printStackTrace();
                return null;
            }
        }
        return bot;
    }

    @Override
    protected boolean isDone() {
        return false;
    }

    @Override
    protected void after() {
        for (Bot bot : botList) {
            bot.disconnect("disconnect");
        }
    }
}
