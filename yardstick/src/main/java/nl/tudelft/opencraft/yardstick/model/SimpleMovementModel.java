package nl.tudelft.opencraft.yardstick.model;

import java.util.Random;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.BlockFace;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

/**
 * Represents a model which moves the bot randomly to short and long distance
 * locations.
 */
public class SimpleMovementModel implements BotModel {

    private static final Random RANDOM = new Random(System.nanoTime());

    @Override
    public TaskExecutor newTask(Bot bot) {
        return new WalkTaskExecutor(bot, newTargetLocation(bot));
    }

    public Vector3i newTargetLocation(Bot bot) {
//        if (RANDOM.nextDouble() < 0.1) {
//            return getNewLongDistanceTarget(bot);
//        } else {
            return getNewFieldLocation(bot);
//        }
    }

    /**
     * Function to make bot walk in a specific area.
     *
     * @return New random location in a field that has the original location at
     * its center.
     */
    private Vector3i getNewFieldLocation(Bot bot) {
        int side = 32;
        Vector3d originalLocation = bot.getPlayer().getLocation();
        int maxx = ((int) originalLocation.getX()) + side / 2;
        int minx = ((int) originalLocation.getX()) - side / 2;
        int maxz = ((int) originalLocation.getZ()) + side / 2;
        int minz = ((int) originalLocation.getZ()) - side / 2;

        int newX = (int) (Math.floor(RANDOM.nextInt(maxx - minx) + minx) + 0.5);
        int newZ = (int) (Math.floor(RANDOM.nextInt(maxz - minz) + minz) + 0.5);

        return getTargetAt(bot, newX, newZ);
    }

    private Vector3i getNewLongDistanceTarget(Bot bot) {
        int maxDist = 64 * 5;
        int minDist = 64 * 1;
        int distance = RANDOM.nextInt(maxDist - minDist) + minDist;
        int angle = RANDOM.nextInt(360);

        Vector3d location = bot.getPlayer().getLocation();
        int newX = (int) (Math.floor(location.getX() + (distance * Math.cos(angle))) + 0.5);
        int newZ = (int) (Math.floor(location.getZ() + (distance * Math.sin(angle))) + 0.5);

        return getTargetAt(bot, newX, newZ);
    }

    private Vector3i getTargetAt(Bot bot, int x, int z) {
        Vector3d botLoc = bot.getPlayer().getLocation();

        int startY = Math.max(botLoc.intVector().getY(), 5);
        int y = -1;
        try {
            Block b = bot.getWorld().getBlockAt(x, startY, z);
            for (int i = -5; i <= 5; i++) {
                Block test = b.getRelative(0, i, 0);
                if (test.getMaterial().isTraversable()
                        && !test.getRelative(BlockFace.BOTTOM).getMaterial().isTraversable()) {
                    y = startY + i;
                    break;
                }
            }

            if (y < 0 || y > 255) {
                return botLoc.intVector();
            }

            return new Vector3i(x, y, z);
        } catch (ChunkNotLoadedException ex) {
            bot.getLogger().warning("Bot target not loaded: (" + x + "," + startY + "," + z + ")");
            return botLoc.intVector();
        }
    }

}
