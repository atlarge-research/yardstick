package nl.tudelft.opencraft.yardstick.bot.world;

import nl.tudelft.opencraft.yardstick.util.Vector3i;

public enum BlockFace {

    NORTH(0, 0, -1),
    EAST(1, 0, 0),
    SOUTH(0, 0, 1),
    WEST(-1, 0, 0),
    UP(0, 1, 0),
    DOWN(0, -1, 0);

    private final Vector3i offset;

    private BlockFace(int modX, int modY, int modZ) {
        this.offset = new Vector3i(modX, modY, modZ);
    }

    public Vector3i getOffset() {
        return offset;
    }

}
