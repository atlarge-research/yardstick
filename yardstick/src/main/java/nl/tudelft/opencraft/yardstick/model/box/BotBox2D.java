package nl.tudelft.opencraft.yardstick.model.box;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.model.TargetLocation;
import nl.tudelft.opencraft.yardstick.util.Vector2i;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class BotBox2D implements Box2D {

    private final int diameter;
    private final TargetLocation targetLocation = new TargetLocation();
    private final Map<Bot, Vector2i> anchorMap = new ConcurrentHashMap<>();

    public BotBox2D(int diameter) {
        this.diameter = diameter;
    }

    @Override
    public Vector3i computeNewLocation(Bot bot) throws ChunkNotLoadedException {
        return targetLocation.newTargetLocation(
                anchorMap.computeIfAbsent(bot, b -> {
                    var pos = b.getPlayer().getLocation().intVector();
                    return new Vector2i(pos.getX(), pos.getZ());
                }),
                diameter,
                bot
        );
    }
}
