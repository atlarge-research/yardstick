package nl.tudelft.opencraft.yardstick.model.box;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.model.TargetLocation;
import nl.tudelft.opencraft.yardstick.util.Vector2i;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class AbsoluteBox2D implements Box2D {

    private final TargetLocation targetLocation = new TargetLocation();
    private final int diameter;
    private final Vector2i center;

    public AbsoluteBox2D(int diameter, Vector2i center) {
        this.diameter = diameter;
        this.center = center;
    }

    @Override
    public Vector3i computeNewLocation(Bot bot) throws ChunkNotLoadedException {
        return targetLocation.newTargetLocation(center, diameter, bot);
    }
}
