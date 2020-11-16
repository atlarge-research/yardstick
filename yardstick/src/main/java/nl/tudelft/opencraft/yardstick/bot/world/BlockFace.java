package nl.tudelft.opencraft.yardstick.bot.world;

import java.util.EnumMap;
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
    private static final EnumMap<BlockFace, BlockFace> OPPOSITE = new EnumMap<>(BlockFace.class);
    //
    private final Vector3i offset;

    static {
        for (BlockFace face : values()) {
            VECTOR3I_TO_BLOCKFACE.put(face.offset, face);
        }
        OPPOSITE.put(BOTTOM, TOP);
        OPPOSITE.put(TOP, BOTTOM);
        OPPOSITE.put(NORTH, SOUTH);
        OPPOSITE.put(SOUTH, NORTH);
        OPPOSITE.put(WEST, EAST);
        OPPOSITE.put(EAST, WEST);
        OPPOSITE.put(SPECIAL, SPECIAL);
    }

    private BlockFace(int modX, int modY, int modZ) {
        this.offset = new Vector3i(modX, modY, modZ);
    }

    public Vector3i getOffset() {
        return offset;
    }

    public BlockFace getOpposite() {
        return OPPOSITE.get(this);
    }

    public static BlockFace forUnitVector(Vector3i vec) {
        return VECTOR3I_TO_BLOCKFACE.get(vec);
    }

    public science.atlarge.opencraft.mcprotocollib.data.game.world.block.BlockFace getInternalFace() {
        // RIP clean code
        return science.atlarge.opencraft.mcprotocollib.data.game.world.block.BlockFace.values()[ordinal()];
    }
}
