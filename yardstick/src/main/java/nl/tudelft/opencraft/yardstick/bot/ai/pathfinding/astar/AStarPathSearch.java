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

import java.util.*;
import java.util.concurrent.PriorityBlockingQueue;
import nl.tudelft.opencraft.yardstick.util.Vector3i;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.BlockPathNode;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.Heuristic;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.PathNode;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.PathSearch;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.PathSearchProvider;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.WorldPhysics;

public class AStarPathSearch implements PathSearch {

    private static final PathNodeComparator PATH_NODE_COMPARATOR = new PathNodeComparator();

    private final AStarPathSearchProvider provider;
    private final Heuristic heuristic;
    private final WorldPhysics physics;
    private final Vector3i start, end;

    private PathNode first, last, complete, completeReverse;

    private Queue<PathNode> openSet, closedSet, openSetReverse, closedSetReverse;
    private Map<Vector3i, PathNode> nodeWorld, nodeWorldReverse;

    public AStarPathSearch(AStarPathSearchProvider provider, Vector3i start, Vector3i end) {
        this.provider = provider;
        this.start = start;
        this.end = end;

        heuristic = provider.getHeuristic();
        physics = provider.getWorldPhysics();

        nodeWorld = new HashMap<Vector3i, PathNode>();
        first = new BlockPathNode(this, start);
        first.setCost(0);
        first.setCostEstimate(heuristic.calculateCost(start, end));
        openSet = new PriorityBlockingQueue<>(64, PATH_NODE_COMPARATOR);
        closedSet = new PriorityBlockingQueue<>(64, PATH_NODE_COMPARATOR);
        nodeWorld.put(start, first);
        openSet.offer(first);

        nodeWorldReverse = new HashMap<Vector3i, PathNode>();
        last = new BlockPathNode(this, end);
        last.setCost(0);
        last.setCostEstimate(heuristic.calculateCost(end, start));
        openSetReverse = new PriorityBlockingQueue<>(64, PATH_NODE_COMPARATOR);
        closedSetReverse = new PriorityBlockingQueue<>(64, PATH_NODE_COMPARATOR);
        nodeWorldReverse.put(end, last);
        openSetReverse.offer(last);
    }

    @Override
    public void step() {
        if (isDone()) {
            return;
        }

        PathNode current = openSet.poll();

        if (complete == null && current.getLocation().equals(end)) {
            complete = reconstructPath(current);
            return;
        }
        calculate(current, false);

        if (completeReverse != null) {
            return;
        }

        PathNode currentReverse = openSetReverse.poll();

        if (completeReverse == null && start.equals(currentReverse.getLocation())) {
            completeReverse = reconstructPath(currentReverse);
        } else if (completeReverse == null) {
            calculate(currentReverse, true);
        }
    }

    private void calculate(PathNode current, boolean reverse) {
        Vector3i location = current.getLocation();

        Map<Vector3i, PathNode> nodeWorld = (reverse ? nodeWorldReverse : this.nodeWorld);
        Queue<PathNode> openSet = (reverse ? openSetReverse : this.openSet);
        Queue<PathNode> closedSet = (reverse ? closedSetReverse : this.closedSet);

        closedSet.offer(current);
        for (Vector3i adjacentLocation : physics.findAdjacent(current.getLocation())) {
            PathNode adjacent;
            if (!nodeWorld.containsKey(adjacentLocation)) {
                adjacent = new BlockPathNode(this, adjacentLocation);
                adjacent.setPrevious(current);
                nodeWorld.put(adjacentLocation, adjacent);
            } else {
                adjacent = nodeWorld.get(adjacentLocation);
            }

            if (closedSet.contains(adjacent)) {
                continue;
            }
            if (!physics.canWalk(location, adjacentLocation)) {
                continue;
            }
            if (reverse && !physics.canWalk(adjacentLocation, location)) {
                continue;
            }

            double cost = current.getCost() + heuristic.calculateCost(location, adjacentLocation);

            boolean contained = openSet.contains(adjacent);
            if (!contained || cost < adjacent.getCost()) {
                if (!contained) {
                    openSet.offer(adjacent);
                }
                adjacent.setPrevious(current);
                current.setNext(adjacent);
                adjacent.setCost(cost);
                adjacent.setCostEstimate(cost + heuristic.calculateCost(adjacentLocation, reverse ? start : end));
            }
        }
    }

    private PathNode reconstructPath(PathNode end) {
        PathNode current = end.getPrevious(), next = end;
        while (current != null) {
            current.setNext(next);
            next = current;
            current = next.getPrevious();
        }
        return next;
    }

    @Override
    public boolean isDone() {
        return complete != null || openSet.isEmpty() || (openSetReverse.isEmpty() && completeReverse == null);
    }

    @Override
    public Vector3i getStart() {
        return start;
    }

    @Override
    public Vector3i getEnd() {
        return end;
    }

    @Override
    public PathNode getPath() {
        return complete;
    }

    @Override
    public PathSearchProvider getSource() {
        return provider;
    }

    private static final class PathNodeComparator implements Comparator<PathNode> {

        @Override
        public int compare(PathNode node1, PathNode node2) {
            return Double.compare(node1.getCostEstimate(), node2.getCostEstimate());
        }
    }
}
