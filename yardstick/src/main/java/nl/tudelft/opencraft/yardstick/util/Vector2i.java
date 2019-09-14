package nl.tudelft.opencraft.yardstick.util;

import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.bot.world.World;

public class Vector2i {
    private final int x;
    private final int z;

    public Vector2i(int x, int z) {
        this.x = x;
        this.z = z;
    }

    public Vector3i getHighestWalkTarget(World world) throws ChunkNotLoadedException {
        return new Vector3i(x, world.getHighestBlockAt(x, z).getY() + 1, z);
    }

    public int getX() {
        return x;
    }

    public int getZ() {
        return z;
    }
}
