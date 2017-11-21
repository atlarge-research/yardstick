package nl.tudelft.opencraft.yardstick.bot.world;

import java.util.HashMap;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public enum BlockFace {

    BOTTOM(0, -1, 0),
    TOP(0, 1, 0),
    NORTH(0, 0, -1),
    SOUTH(0, 0, 1),
    WEST(-1, 0, 0),
    EAST(1, 0, 0),
    SPECIAL(0, 0, 0);

    private static final HashMap<Vector3i, BlockFace> VECTOR3I_TO_BLOCKFACE = new HashMap<>();
    private final Vector3i offset;

    static {
        for (BlockFace face : values()) {
            VECTOR3I_TO_BLOCKFACE.put(face.offset, face);
        }
    }

    private BlockFace(int modX, int modY, int modZ) {
        this.offset = new Vector3i(modX, modY, modZ);
    }

    public Vector3i getOffset() {
        return offset;
    }

    public static BlockFace forUnitVector(Vector3i vec) {
        return VECTOR3I_TO_BLOCKFACE.get(vec);
    }

    public com.github.steveice10.mc.protocol.data.game.world.block.BlockFace getInternalFace() {
        // RIP clean code
        return com.github.steveice10.mc.protocol.data.game.world.block.BlockFace.values()[ordinal()];
    }
}
