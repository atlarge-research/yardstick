package nl.tudelft.opencraft.yardstick.model.box;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.model.TargetLocation;
import nl.tudelft.opencraft.yardstick.util.Vector2i;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class WorldSpawnBox2D implements Box2D {

    private final TargetLocation targetLocation = new TargetLocation();
    private final int diameter;
    private Vector2i worldSpawnPoint;

    public WorldSpawnBox2D(int diameter) {
        this.diameter = diameter;
    }

    @Override
    public Vector3i computeNewLocation(Bot bot) throws ChunkNotLoadedException {
        if (worldSpawnPoint == null) {
            var spawn = bot.getWorld().getSpawnPoint();
            worldSpawnPoint = new Vector2i(spawn.getX(), spawn.getZ());
        }
        return targetLocation.newTargetLocation(worldSpawnPoint, diameter, bot);
    }
}
