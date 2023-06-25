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

package nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.astar;

import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Set;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.BlockPathNode;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.PathNode;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.astar.heuristic.Heuristic;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.bot.world.WorldPhysics;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class SimpleAStar {

    private final Heuristic heuristic;
    private final WorldPhysics worldPhysics;

    public SimpleAStar(Heuristic heuristic, WorldPhysics physics) {
        this.heuristic = heuristic;
        this.worldPhysics = physics;
    }

    public PathNode search(Vector3i start, Vector3i end) throws ChunkNotLoadedException {
        Map<Vector3i, PathNode> nodeMap = new HashMap<>();
        Set<PathNode> visited = new HashSet<>();

        PriorityQueue<PathNode> toVisit = new PriorityQueue<>(Comparator.comparingDouble(thisNode
                -> thisNode.getCost() + heuristic.calculateCost(thisNode.getLocation().doubleVector(), end.doubleVector())
        ));

        PathNode startNode = new PathNode(start);
        startNode.setCost(0);
        nodeMap.put(start, startNode);
        toVisit.add(startNode);

        while (!toVisit.isEmpty() && !Thread.interrupted()) {
            PathNode current = toVisit.poll();
            visited.add(current);

            if (current.getLocation().distanceSquared(end) <= 1 && worldPhysics.canWalk(current.getLocation(), end)) {
                PathNode endNode = new PathNode(end, current, null);
                return buildPath(endNode);
            }

            Set<PathNode> neigborNodes = new HashSet<>();
            for (Vector3i vec : worldPhysics.findWalkable(current.getLocation())) {
                if (vec == null) {
                    continue;
                }

                // Discover neighbour
                if (nodeMap.containsKey(vec)) {
                    neigborNodes.add(nodeMap.get(vec));
                } else {
                    BlockPathNode node = new BlockPathNode(vec);
                    node.setCost(current.getCost() + 1);
                    node.setPrevious(current);
                    neigborNodes.add(node);
                    nodeMap.put(vec, node);
                }
            }

            for (PathNode neighbor : neigborNodes) {
                if (visited.contains(neighbor)) {
                    continue;
                }

                if (!toVisit.contains(neighbor)) {
                    toVisit.add(neighbor);
                } else if (toVisit.contains(neighbor) && neighbor.getCost() > current.getCost() + 1) {
                    toVisit.remove(neighbor);
                    neighbor.setCost(current.getCost() + 1);
                    neighbor.setPrevious(current);
                    toVisit.add(neighbor);
                }
            }
        }
        return null;
    }

    private PathNode buildPath(PathNode end) {
        PathNode pointer = end;
        while (pointer.getPrevious() != null) {
            pointer.getPrevious().setNext(pointer);
            pointer = pointer.getPrevious();
        }
        return pointer;
    }

    public Heuristic getHeuristic() {
        return heuristic;
    }

    public WorldPhysics getWorldPhysics() {
        return worldPhysics;
    }
}
