package nl.tudelft.opencraft.yardstick.bot.ai.task;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector2i;

public class WalkXZTask implements Task {

    private Vector2i target;

    public Vector2i getTarget() {
        return target;
    }

    public void setTarget(Vector2i target) {
        this.target = target;
    }

    @Override
    public TaskExecutor toExecutor(Bot bot) {
        try {
            return new WalkTaskExecutor(bot, target.getHighestWalkTarget(bot.getWorld()));
        } catch (ChunkNotLoadedException e) {
            bot.getLogger().warning(e.getMessage());
            return new WalkTaskExecutor(bot, bot.getPlayer().getLocation().intVector());
        }
    }
}
