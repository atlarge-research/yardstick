package nl.tudelft.opencraft.yardstick.model.box;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public interface Box2D {
    Vector3i computeNewLocation(Bot bot) throws ChunkNotLoadedException;
}
