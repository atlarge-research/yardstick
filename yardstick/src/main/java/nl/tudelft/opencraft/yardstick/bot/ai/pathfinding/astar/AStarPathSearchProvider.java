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
package nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.astar;

import nl.tudelft.opencraft.yardstick.util.Vector3i;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.Heuristic;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.PathSearchProvider;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.WorldPhysics;
import nl.tudelft.opencraft.yardstick.bot.world.World;

public class AStarPathSearchProvider implements PathSearchProvider {

    private final Heuristic heuristic;
    private final WorldPhysics worldPhysics;

    private final World world;

    public AStarPathSearchProvider(Heuristic heuristic, WorldPhysics worldPhysics) {
        this.heuristic = heuristic;
        this.worldPhysics = worldPhysics;

        world = worldPhysics.getWorld();
    }

    @Override
    public AStarPathSearch provideSearch(Vector3i start, Vector3i end) {
        return new AStarPathSearch(this, start, end);
    }

    @Override
    public Heuristic getHeuristic() {
        return heuristic;
    }

    @Override
    public WorldPhysics getWorldPhysics() {
        return worldPhysics;
    }

    @Override
    public World getWorld() {
        return world;
    }
}
