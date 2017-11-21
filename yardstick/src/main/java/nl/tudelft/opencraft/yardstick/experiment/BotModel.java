package nl.tudelft.opencraft.yardstick.experiment;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.Task;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTask;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class BotModel {

    private static final double INTERACT_TO_MOVEMENT = 0.5;
    //
    private final InteractionModel interact = new InteractionModel();
    private final MovementModel movement = new MovementModel();

    public Task nextTask(Bot bot) {
        if (Math.random() < INTERACT_TO_MOVEMENT) {
            // Interact

        } else {
            // Movement
            Vector3i newLocation = movement.newTargetLocation(bot);
            bot.getLogger().info(String.format("Setting task for bot to walk to %s", newLocation));
            bot.setTask(new WalkTask(bot, newLocation));
        }
    }

}
