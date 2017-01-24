package nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.astar;

import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.*;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

import java.util.*;

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
        Map<PathNode, Integer> visited = new HashMap<>();
        PriorityQueue<PathNode> locations = new PriorityQueue<>();
        PathNode startNode = new BlockPathNode(start, 0);
        locations.add(startNode);
        while (!locations.isEmpty()) {
            PathNode current = locations.poll();
            visited.put(current, current.getCost());
            if (current.getLocation().equals(end)) {
                return buildPath(current);
            } else {
                for (Vector3i neighbor : worldPhysics.findAdjacent(current.getLocation())) {
                    if (worldPhysics.canWalk(current.getLocation(), neighbor)) {
                        int expectedCost = current.getCost() + 1 + heuristic.calculateCost(neighbor, end);
                        PathNode node = new BlockPathNode(neighbor, expectedCost);
                        if (!visited.containsKey(node)
                                || (visited.containsKey(node) && expectedCost < visited.get(node))) {
                            visited.put(node, expectedCost);
                            if (locations.contains(node)) {
                                locations.remove(node);
                            }
                            locations.add(node);
                            node.setPrevious(current);
                        }
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
