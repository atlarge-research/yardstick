package nl.tudelft.opencraft.yardstick.playerbehavior;

public interface World {
    Vector3i getTopBlock(int x, int z);

    boolean playerCanStandOn(Vector3i location);
}
