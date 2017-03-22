/*
Copyright (c) 2013, DarkStorm (darkstorm@evilminecraft.net)
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
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
        int x = locA.getX(), y = locA.getY(), z = locA.getZ();
        int x2 = locB.getX(), y2 = locB.getY(), z2 = locB.getZ();
        if (y2 <= 0) {
            return false;
        }

        //
        // Check destination
        //
        boolean valid = true;
        valid = valid && isTraversable(x2, y2, z2); // Block at must be non-solid
        valid = valid && isTraversable(x2, y2 + 1, z2); // Block above must be non-solid

        // Avoid lava
        Material lowerMat = world.getBlockAt(x2, y2 - 1, z2).getMaterial();
        valid = valid && lowerMat != Material.LAVA;
        valid = valid && lowerMat != Material.STATIONARY_LAVA;

        //
        // Check origin
        //
        // If there is an empty block under the origin
        if (isTraversable(x, y - 1, z)) {
            valid = valid
                    && ((y2 < y && x2 == x && z2 == z)
                    || ((canClimb(locA) && canClimb(locB)) || (!canClimb(locA) && canClimb(locB)) || (canClimb(locA)
                    && !canClimb(locB) && (x2 == x && z2 == z ? true : !isTraversable(x2, y2 - 1, z2))))
                    || !isTraversable(x2, y2 - 1, z2));

            /* // TODO: Further investigate this:
            boolean vertical = x2 == x && z2 == z;
            boolean downWards = vertical && y2 < y;
            boolean bothClimbable = canClimb(locA) && canClimb(locB);
            boolean bClimbable = !canClimb(locA) && canClimb(locB);
            boolean aClimbable = canClimb(locA) && !canClimb(locB);
            boolean solidUnderLocB = !isTraversable(x2, y2 - 1, z2);

            valid = valid
                    && (downWards
                    || (bothClimbable || bClimbable || (aClimbable && (vertical ? true : solidUnderLocB)))
                    || solidUnderLocB);
             */
        }

        if (y != y2 && (x != x2 || z != z2)) {
            return false;
        }

        if (x != x2 && z != z2) {
            // TODO: Investigate this
            valid = valid && isTraversable(x2, y, z);
            valid = valid && isTraversable(x, y, z2);
            valid = valid && isTraversable(x2, y + 1, z);
            valid = valid && isTraversable(x, y + 1, z2);
            if (y != y2) {
                valid = valid && isTraversable(x2, y2, z);
                valid = valid && isTraversable(x, y2, z2);
                valid = valid && isTraversable(x, y2, z);
                valid = valid && isTraversable(x2, y, z2);
                valid = valid && isTraversable(x2, y + 1, z2);
                valid = valid && isTraversable(x, y2 + 1, z);
                valid = false;
            }
        } else if (x != x2 && y != y2) {
            valid = valid && isTraversable(x2, y, z);
            valid = valid && isTraversable(x, y2, z);
            if (y > y2) {
                valid = valid && isTraversable(x2, y + 1, z);
            } else {
                valid = valid && isTraversable(x, y2 + 1, z);
            }
            valid = false;
        } else if (z != z2 && y != y2) {
            valid = valid && isTraversable(x, y, z2);
            valid = valid && isTraversable(x, y2, z);
            if (y > y2) {
                valid = valid && isTraversable(x, y + 1, z2);
            } else {
                valid = valid && isTraversable(x, y2 + 1, z);
            }
            valid = false;
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
        return world.getBlockAt(x, y, z).getMaterial().isTraversable();
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
