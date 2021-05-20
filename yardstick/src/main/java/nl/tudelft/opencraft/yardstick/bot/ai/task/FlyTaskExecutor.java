package nl.tudelft.opencraft.yardstick.bot.ai.task;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

/**
 * In order to avoid obstacles, the bot first flies to the maximum altitude,
 * then flies to the target (X, Z) coordinates, then descends to meet the Y target
 */
public class FlyTaskExecutor extends AbstractTaskExecutor {

    public static final int maxY = 150;
    private static final double speedY = 1;
    private final double speedXZ;

    private Vector3i target;

    public FlyTaskExecutor(final Bot bot, Vector3i targetLocation, double speed) {
        super(bot);

        this.target = targetLocation;
        if (bot.getPlayer().getLocation().intVector().equals(target)) {
            logger.warning("Useless fly task. Bot and given target location equal.");
        }

        speedXZ = speed;
    }

    @Override
    protected TaskStatus onTick() {
        // todo: perform additional checks for flying into objects

        Vector3d nextLocation = bot.getPlayer().getLocation();
        Vector3i currentLocation = nextLocation.intVector();
        int currX = currentLocation.getX(), currZ = currentLocation.getZ();

        // check we have arrived
        if (currentLocation.equals(target)) {
            return TaskStatus.forSuccess();
        }

        // check if we have to descend
        if (currX == target.getX() && currZ == target.getZ()) {
            try {
                int highestY = bot.getWorld().getHighestBlockAt(currX, currZ).getY();
                // check we can actually descend; if not, change target
                if (highestY > target.getY()) {
                    target = new Vector3i(currX, highestY, currZ);
                }
            } catch (ChunkNotLoadedException ex) {
                return TaskStatus.forFailure(String.format("Chunk that contains block %s not loaded", currentLocation));
            }

            double toDescend = -Math.min(nextLocation.getY() - (double) target.getY(), speedY);
            nextLocation = nextLocation.add(0, toDescend, 0);
        } else if (currentLocation.getY() < maxY) {
            // we have to ascend
            double toAscend = Math.min((double) maxY - nextLocation.getY(), speedY);
            nextLocation = nextLocation.add(0, toAscend, 0);
        } else {
            // calculate delta movement
            double diffX = Math.abs((double) target.getX() - nextLocation.getX());
            double diffZ = Math.abs((double) target.getZ() - nextLocation.getZ());
            double moveX = Math.min(diffX, speedXZ);
            double moveZ = Math.min(diffZ, speedXZ);

            // adjust for angle
            if (diffX < diffZ) {
                moveX *= diffX / diffZ;
            } else {
                moveZ *= diffZ / diffX;
            }

            // account for direction
            if (target.getX() < nextLocation.getX()) moveX *= -1;
            if (target.getZ() < nextLocation.getZ()) moveZ *= -1;

            nextLocation = nextLocation.add(moveX, 0, moveZ);
        }

        // report location to server
        bot.getController().updateLocation(nextLocation);
        return TaskStatus.forInProgress();
    }

    @Override
    protected void onStop() {}
}
