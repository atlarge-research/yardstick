package nl.tudelft.opencraft.yardstick.bot.ai.pathfinding;

import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.astar.heuristic.Heuristic;
import nl.tudelft.opencraft.yardstick.bot.world.WorldPhysics;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

// Creates a path of a flat, repeating path. Warning: Path has no end
public class FixedCircle {
    private final WorldPhysics worldPhysics;

    public FixedCircle(WorldPhysics physics) {
        this.worldPhysics = physics;
    }

    public PathNode getCirclePath(Vector3i start, int squareSize){
        PathNode startNode = new PathNode(start);
        //PathNode endNode = new PathNode(start);
        PathNode current = startNode;
        // -x
        for(int i = 1; i < squareSize; i++){
            int prevY= current.getLocation().getY();
            int prevX= current.getLocation().getX();
            int prevZ= current.getLocation().getZ();
            Vector3i newLoc = new Vector3i(prevX-1,prevY,prevZ);
            PathNode newNode = new PathNode(newLoc);
            current.setNext(newNode);
            newNode.setPrevious(current);
            current = newNode;
        }
        // -z
        for(int i = 1; i < squareSize; i++){
            int prevY= current.getLocation().getY();
            int prevX= current.getLocation().getX();
            int prevZ= current.getLocation().getZ();
            Vector3i newLoc = new Vector3i(prevX,prevY,prevZ-1);
            PathNode newNode = new PathNode(newLoc);
            current.setNext(newNode);
            newNode.setPrevious(current);
            current = newNode;
        }
        // +x            current.setNext(newNode);
        for(int i = 1; i < squareSize; i++){
            int prevY= current.getLocation().getY();
            int prevX= current.getLocation().getX();
            int prevZ= current.getLocation().getZ();
            Vector3i newLoc = new Vector3i(prevX+1,prevY,prevZ);
            PathNode newNode = new PathNode(newLoc);
            current.setNext(newNode);
            newNode.setPrevious(current);
            current = newNode;
        }
        // +z
        for(int i = 1; i < squareSize-1; i++){
            int prevY= current.getLocation().getY();
            int prevX= current.getLocation().getX();
            int prevZ= current.getLocation().getZ();
            Vector3i newLoc = new Vector3i(prevX,prevY,prevZ+1);
            PathNode newNode = new PathNode(newLoc);
            current.setNext(newNode);
            newNode.setPrevious(current);
            current = newNode;
        }
        current.setNext(startNode);
        startNode.setPrevious(current);
        return startNode;
    }

    public WorldPhysics getWorldPhysics() {
        return worldPhysics;
    }

}
