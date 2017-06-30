package nl.tudelft.opencraft.yardstick.experiment;

import java.util.Random;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class MovementModel {

    private static final Random random = new Random(System.currentTimeMillis());

    public Vector3i newTargetLocation(Bot bot) {
        if (random.nextDouble() < 0.1) {
            return getNewLongDistanceTarget(bot);
        } else {
            return getNewFieldLocation(bot);
        }
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

        int newX = (int) (Math.floor(random.nextInt(maxx - minx) + minx) + 0.5);
        int newZ = (int) (Math.floor(random.nextInt(maxz - minz) + minz) + 0.5);

        try {
            int newY = bot.getWorld().getHighestBlockAt(newX, newZ).getY() + 1;
            return new Vector3i(newX, newY, newZ);
        } catch (ChunkNotLoadedException ex) {
            return originalLocation.intVector();
        }
    }

    private Vector3i getNewLongDistanceTarget(Bot bot) {
        int maxDist = 64 * 5;
        int minDist = 64 * 1;
        int distance = random.nextInt(maxDist - minDist) + minDist;
        int angle = random.nextInt(360);

        Vector3d location = bot.getPlayer().getLocation();
        int newX = (int) (Math.floor(location.getX() + (distance * Math.cos(angle))) + 0.5);
        int newZ = (int) (Math.floor(location.getZ() + (distance * Math.sin(angle))) + 0.5);

        try {
            int newY = bot.getWorld().getHighestBlockAt(newX, newZ).getY() + 1;
            return new Vector3i(newX, newY, newZ);
        } catch (ChunkNotLoadedException ex) {
            return location.intVector();
        }
    }

}
