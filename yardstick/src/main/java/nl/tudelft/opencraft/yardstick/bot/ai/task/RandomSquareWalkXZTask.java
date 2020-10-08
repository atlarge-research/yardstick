package nl.tudelft.opencraft.yardstick.bot.ai.task;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector2i;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

import java.util.Random;

public class RandomSquareWalkXZTask implements Task {

    private Vector2i center;
    private int radius;

    public Vector2i getCenter() {
        return center;
    }

    public void setCenter(Vector2i center) {
        this.center = center;
    }

    public int getRadius() {
        return radius;
    }

    public void setRadius(int radius) {
        this.radius = radius;
    }

    @Override
    public TaskExecutor toExecutor(Bot bot) {
        Random random = new Random();
        int x = random.nextInt() % ((2 * radius) + 1) + center.getX();
        int z = random.nextInt() % ((2 * radius) + 1) + center.getZ();
        Vector2i v = new Vector2i(x, z);
        Vector3i target;
        try {
            target = v.getHighestWalkTarget(bot.getWorld());
        } catch (ChunkNotLoadedException e) {
            bot.getLogger().warning(e.getMessage());
            target = bot.getPlayer().getLocation().intVector();
        }
        return new WalkTaskExecutor(bot, target);
    }
}
