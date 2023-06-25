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
 *
 * Copyright (c) 2013, DarkStorm (darkstorm@evilminecraft.net)
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 * list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation
 * and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
 * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
package nl.tudelft.opencraft.yardstick.bot.world;

import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class SimpleWorldPhysics implements WorldPhysics {

    private static final Vector3i[] SURROUNDING = new Vector3i[]{
        // middle --- y + 0
        new Vector3i(-1, 0, 1),
        new Vector3i(0, 0, 1),
        new Vector3i(1, 0, 1),
        new Vector3i(-1, 0, 0),
        new Vector3i(1, 0, 0),
        new Vector3i(-1, 0, -1),
        new Vector3i(0, 0, -1),
        new Vector3i(1, 0, -1),
        // bottom --- y - 1
        new Vector3i(-1, -1, 1),
        new Vector3i(0, -1, 1),
        new Vector3i(1, -1, 1),
        new Vector3i(-1, -1, 0),
        new Vector3i(0, -1, 0),
        new Vector3i(1, -1, 0),
        new Vector3i(-1, -1, -1),
        new Vector3i(0, -1, -1),
        new Vector3i(1, -1, -1),
        // top  --- y + 1
        new Vector3i(-1, 1, 1),
        new Vector3i(0, 1, 1),
        new Vector3i(1, 1, 1),
        new Vector3i(-1, 1, 0),
        new Vector3i(0, 1, 0),
        new Vector3i(1, 1, 0),
        new Vector3i(-1, 1, -1),
        new Vector3i(0, 1, -1),
        new Vector3i(1, 1, -1),};

    private final World world;

    public SimpleWorldPhysics(World world) {
        this.world = world;
    }

    @Override
    public Vector3i[] findAdjacent(Vector3i location) {
        Vector3i[] locations = new Vector3i[SURROUNDING.length];
        for (int i = 0; i < locations.length; i++) {
            locations[i] = location.add(SURROUNDING[i]);
        }
        return locations;
    }

    public Vector3i[] findWalkable(Vector3i from) throws ChunkNotLoadedException {

        Vector3i[] walkable = new Vector3i[SURROUNDING.length];

        int i = 0;
        for (Vector3i offset : SURROUNDING) {
            Vector3i target = from.add(offset);
            if (canWalk(from, target)) {
                walkable[i++] = target;
            }
        }

        return walkable;
    }

    /**
     * Determines if a player is able to traverse adjacent locations: from
     * location A to location B.
     *
     * @param locA The origin location.
     * @param locB The destination location.
     * @return True if the player can traverse.
     * @throws ChunkNotLoadedException If there is not enough information in the
     * system to determine traversal.
     */
    @Override
    public boolean canWalk(Vector3i locA, Vector3i locB) throws ChunkNotLoadedException {
        int origX = locA.getX(), origY = locA.getY(), origZ = locA.getZ();
        int destX = locB.getX(), destY = locB.getY(), destZ = locB.getZ();

        //
        // Validity checks
        //
        // Destination and origin must be 1 apart at most
        boolean valid = true;
        if (Math.abs(origX - destX) > 1) {
            valid = false;
        }
        if (Math.abs(origY - destY) > 1) {
            valid = false;
        }
        if (Math.abs(origZ - destZ) > 1) {
            valid = false;
        }
        if (!valid) {
            throw new IllegalArgumentException("Invalid move: " + locA + " -> " + locB + ". Origin and destination too far apart!");
        }

        // Origin must be traversable
        valid = valid && isTraversable(origX, origY, origZ);
        valid = valid && isTraversable(origX, origY + 1, origZ);

        if (!valid) {
            throw new IllegalArgumentException("Invalid move: " + locA + " -> " + locB + ". Origin not walkable!");
        }

        //
        // Path checking
        //
        // Destination must have Y > 0
        if (destY <= 0) {
            return false;
        }

        //
        // Destination must be traversable
        valid = valid && isTraversable(destX, destY, destZ);
        valid = valid && isTraversable(destX, destY + 1, destZ);

        // Avoid lava
        Material lowerMat = world.getBlockAt(destX, destY - 1, destZ).getMaterial();
        valid = valid && lowerMat != Material.LAVA;
        valid = valid && lowerMat != Material.STATIONARY_LAVA;

        // Avoid fences
        valid = valid && lowerMat != Material.FENCE;
        valid = valid && lowerMat != Material.FENCE_GATE;
        valid = valid && lowerMat != Material.ACADIA_FENCE;
        valid = valid && lowerMat != Material.ACADIA_FENCE_GATE;
        valid = valid && lowerMat != Material.BIRCH_FENCE;
        valid = valid && lowerMat != Material.BIRCH_FENCE_GATE;
        valid = valid && lowerMat != Material.DARK_OAK_FENCE;
        valid = valid && lowerMat != Material.DARK_OAK_FENCE_GATE;
        valid = valid && lowerMat != Material.JUNGLE_FENCE;
        valid = valid && lowerMat != Material.JUNGLE_FENCE_GATE;
        valid = valid && lowerMat != Material.NETHER_FENCE;
        //valid = valid && lowerMat != Material.NETHER_FENCE_GATE; // Doesn't exist
        valid = valid && lowerMat != Material.SPRUCE_FENCE;
        valid = valid && lowerMat != Material.SPRUCE_FENCE_GATE;

        // Only one coord at a time
        boolean movingX = origX != destX;
        boolean movingY = origY != destY;
        boolean movingZ = origZ != destZ;

        // Only allow single axis movement for now
        valid = valid
                && ((movingX && !movingY && !movingZ)
                || (!movingX && movingY && !movingZ)
                || (!movingX && !movingY && movingZ));

        // If we're staying level
        if (destY == origY) {
            // Origin or dest must have a block
            boolean origUnder = !isTraversable(origX, origY - 1, origZ);
            boolean destUnder = !isTraversable(destX, destY - 1, destZ);

            valid = valid && (origUnder || destUnder);

            // Destination must have a solid block at least 3 blocks under
            valid = valid && (!isTraversable(destX, destY - 1, destZ)
                    || !isTraversable(destX, destY - 2, destZ)
                    || !isTraversable(destX, destY - 3, destZ));
        }

        // If we're jumping
        if (destY > origY) {
            // There must be a block below the origin
            valid = valid && !isTraversable(origX, origY - 1, origZ);

            // There must be a block next to us (efficiency)
            valid = valid
                    && (!isTraversable(origX + 1, origY, origZ)
                    || !isTraversable(origX - 1, destY, origZ)
                    || !isTraversable(origX, origY, origZ + 1)
                    || !isTraversable(origX, origY, origZ - 1));
        }

        // If we're falling
        if (destY < origY) {
            // Origin block may not be fluid (drowning)
            Material mat = world.getBlockAt(origX, origY, origZ).getMaterial();
            valid = valid && !mat.isFluid();
        }

        return valid;
    }

    @Override
    public boolean canClimb(Vector3i location) throws ChunkNotLoadedException {
        int id = world.getBlockAt(location).getTypeId();
        if (id == 8 || id == 9 || id == 65) // Water / Moving Water / Ladder
        {
            return true;
        }
        if (id == 106) { // Vines (which require an adjacent solid block)
            if (!isTraversable(location.getX(), location.getY(), location.getZ() + 1) || !isTraversable(location.getX(), location.getY(), location.getZ() - 1)
                    || !isTraversable(location.getX() + 1, location.getY(), location.getZ()) || !isTraversable(location.getX() - 1, location.getY(), location.getZ())) {
                return true;
            }
        }
        return false;
    }

    /**
     * Returns true if the block at (x,y,z) can be traversed through.
     *
     * @param x The x location of the block.
     * @param y The y location of the block.
     * @param z The z location of the block.
     * @return True if the block is traversable.
     * @throws ChunkNotLoadedException If the block is outside viewing range.
     */
    public boolean isTraversable(int x, int y, int z) throws ChunkNotLoadedException {
        Block block = world.getBlockAt(x, y, z);
        if (block.getChunk() == null) {
            throw new ChunkNotLoadedException(new ChunkLocation(x, z));
        }
        return block.getMaterial().isTraversable();
    }

    public boolean canStand(Vector3i location) throws ChunkNotLoadedException {
        int x = location.getX();
        int y = location.getY();
        int z = location.getZ();
        return !isTraversable(x, y, z) && isTraversable(x, y + 1, z) && isTraversable(x, y + 2, z);
    }

    @Override
    public World getWorld() {
        return world;
    }
}
