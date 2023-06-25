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

package nl.tudelft.opencraft.yardstick.util;

import nl.tudelft.opencraft.yardstick.bot.entity.Player;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.BlockFace;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.bot.world.Material;

/**
 * Represents world-related utilities.
 */
public class WorldUtil {

    private WorldUtil() {
    }

    /**
     * Calculates and selects a visible block face the player can see for a
     * given block if such a face exists. This takes into account the
     * environment (block occlusion).
     *
     * @param player the player.
     * @param block the block the player is observing.
     * @return an arbitrary block face that is visible, or null, if none exists.
     */
    public static BlockFace getVisibleBlockFace(Player player, Block block) {
        BlockFace[] directed = getDirectedBlockFaces(player, block);

        for (int i = 0; i < directed.length; i++) {
            Block relative;
            try {
                relative = block.getRelative(directed[i]);
            } catch (ChunkNotLoadedException ex) {
                continue;
            }

            // Check if the adjacent block is AIR
            if (relative.getMaterial() == Material.AIR) {
                // We got it!
                return directed[i];
            }
        }

        // All block faces are occluded by another block
        return null;
    }

    /**
     * Geometrically calculates the three block faces (potentially) visible to a
     * player looking at a block. This does not take into account the distance
     * (is the player inside the block, or is the block even rendered?) and the
     * surroundings (is there a block or entity occluding the face?).
     *
     * @param player the player.
     * @param block the block the player is observing.
     * @return an array of three block faces.
     */
    public static BlockFace[] getDirectedBlockFaces(Player player, Block block) {
        // Determine the block face
        Vector3d playerLoc = player.getLocation();
        Vector3d blockLoc = block.getLocation().doubleVector().add(0.5, 0.5, 0.5);

        // Calculate unit vector from the center of the block pointing at the player
        Vector3d diff = playerLoc.subtract(blockLoc).unit();

        // Now, the three faces are computed by rounding two components towards zero,
        // and one away from zero.
        BlockFace[] faces = new BlockFace[3];

        int x = diff.getX() > 0 ? 1 : -1;
        faces[0] = BlockFace.forUnitVector(new Vector3i(x, 0, 0));
        int y = diff.getY() > 0 ? 1 : -1;
        faces[1] = BlockFace.forUnitVector(new Vector3i(0, y, 0));
        int z = diff.getZ() > 0 ? 1 : -1;
        faces[2] = BlockFace.forUnitVector(new Vector3i(0, 0, z));

        return faces;
    }

}
