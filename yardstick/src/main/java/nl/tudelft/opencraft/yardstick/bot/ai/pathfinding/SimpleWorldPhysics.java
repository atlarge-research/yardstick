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
package nl.tudelft.opencraft.yardstick.bot.ai.pathfinding;

import nl.tudelft.opencraft.yardstick.util.Vector3i;
import nl.tudelft.opencraft.yardstick.bot.world.World;

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
    private static final boolean[] NON_TRAVERSABLE_TYPES;

    static {
        // TODO
        NON_TRAVERSABLE_TYPES = new boolean[256];
        NON_TRAVERSABLE_TYPES[0] = true;
    }

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

    @Override
    public boolean canWalk(Vector3i location, Vector3i location2) {
        int x = location.getX(), y = location.getY(), z = location.getZ();
        int x2 = location2.getX(), y2 = location2.getY(), z2 = location2.getZ();
        if (y2 < 0) {
            return false;
        }

        boolean valid = true;
        valid = valid && isEmpty(x2, y2, z2); // Block at must be non-solid
        valid = valid && isEmpty(x2, y2 + 1, z2); // Block above must be non-solid

        int lowerBlock = world.getBlockAt(x2, y2 - 1, z2).getTypeId();
        valid = valid && lowerBlock != 10;
        valid = valid && lowerBlock != 11;

        if (isEmpty(x, y - 1, z)) {
            valid = valid
                    && ((y2 < y && x2 == x && z2 == z)
                    || ((canClimb(location) && canClimb(location2)) || (!canClimb(location) && canClimb(location2)) || (canClimb(location)
                    && !canClimb(location2) && (x2 == x && z2 == z ? true : !isEmpty(x2, y2 - 1, z2)))) || !isEmpty(x2, y2 - 1, z2));
        }
        if (y != y2 && (x != x2 || z != z2)) {
            return false;
        }
        if (x != x2 && z != z2) {
            valid = valid && isEmpty(x2, y, z);
            valid = valid && isEmpty(x, y, z2);
            valid = valid && isEmpty(x2, y + 1, z);
            valid = valid && isEmpty(x, y + 1, z2);
            if (y != y2) {
                valid = valid && isEmpty(x2, y2, z);
                valid = valid && isEmpty(x, y2, z2);
                valid = valid && isEmpty(x, y2, z);
                valid = valid && isEmpty(x2, y, z2);
                valid = valid && isEmpty(x2, y + 1, z2);
                valid = valid && isEmpty(x, y2 + 1, z);
                valid = false;
            }
        } else if (x != x2 && y != y2) {
            valid = valid && isEmpty(x2, y, z);
            valid = valid && isEmpty(x, y2, z);
            if (y > y2) {
                valid = valid && isEmpty(x2, y + 1, z);
            } else {
                valid = valid && isEmpty(x, y2 + 1, z);
            }
            valid = false;
        } else if (z != z2 && y != y2) {
            valid = valid && isEmpty(x, y, z2);
            valid = valid && isEmpty(x, y2, z);
            if (y > y2) {
                valid = valid && isEmpty(x, y + 1, z2);
            } else {
                valid = valid && isEmpty(x, y2 + 1, z);
            }
            valid = false;
        }
        int nodeBlockUnder = world.getBlockAt(x2, y2 - 1, z2).getTypeId();
        if (nodeBlockUnder == 85 || nodeBlockUnder == 107 || nodeBlockUnder == 113) {
            valid = false;
        }
        return valid;
    }

    @Override
    public boolean canClimb(Vector3i location) {
        int id = world.getBlockAt(location).getTypeId();
        if (id == 8 || id == 9 || id == 65) // Water / Moving Water / Ladder
        {
            return true;
        }
        if (id == 106) { // Vines (which require an adjacent solid block)
            if (!isEmpty(location.getX(), location.getY(), location.getZ() + 1) || !isEmpty(location.getX(), location.getY(), location.getZ() - 1)
                    || !isEmpty(location.getX() + 1, location.getY(), location.getZ()) || !isEmpty(location.getX() - 1, location.getY(), location.getZ())) {
                return true;
            }
        }
        return false;
    }

    private boolean isEmpty(int x, int y, int z) {
        int id = world.getBlockAt(x, y, z).getTypeId();
        return id >= 0 && id < NON_TRAVERSABLE_TYPES.length && !NON_TRAVERSABLE_TYPES[id];
    }

    @Override
    public World getWorld() {
        return world;
    }
}
