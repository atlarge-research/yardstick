package nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.astar;

import java.util.*;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.*;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

/**
 * Created by jesse on 1/24/17.
 */
public class SaneAStar {

    private final Heuristic heuristic;
    private final WorldPhysics worldPhysics;

    public SaneAStar(Heuristic heuristic, WorldPhysics physics) {
        this.heuristic = heuristic;
        this.worldPhysics = physics;
    }

    public PathNode provideSearch(Vector3i start, Vector3i end) throws ChunkNotLoadedException {
        Map<Vector3i, PathNode> nodeMap = new HashMap<>();
        Set<PathNode> visited = new HashSet<>();
        PriorityQueue<PathNode> toVisit = new PriorityQueue<>(Comparator.comparingInt(thisNode -> thisNode.getCost() + heuristic.calculateCost(thisNode.getLocation(), end)));
        PathNode startNode = new BlockPathNode(start);
        startNode.setCost(0);
        nodeMap.put(start, startNode);
        toVisit.add(startNode);
        while (!toVisit.isEmpty() && !Thread.interrupted()) {
            PathNode current = toVisit.poll();
            visited.add(current);
            if (current.getLocation().equals(end)) {
                return buildPath(current);
            } else {
                Set<PathNode> neigborNodes = new HashSet<>();
                for (Vector3i vec : worldPhysics.findAdjacent(current.getLocation())) {
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

                    try {
                        if (!worldPhysics.canWalk(current.getLocation(), neighbor.getLocation())) {
                            continue;
                        }
                    } catch (ChunkNotLoadedException ex) {
                        // TODO: This is not right
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
