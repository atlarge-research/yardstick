/*
 * Yardstick: A Benchmark for Minecraft-like Services
 * Copyright (C) 2020 AtLarge Research
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

package nl.tudelft.opencraft.yardstick.bot.world;

import nl.tudelft.opencraft.yardstick.util.Vector3i;

import java.util.EnumMap;
import java.util.HashMap;

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
