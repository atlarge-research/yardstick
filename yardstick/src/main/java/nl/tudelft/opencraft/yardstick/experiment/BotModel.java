package nl.tudelft.opencraft.yardstick.experiment;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.Task;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTask;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class BotModel {

    private static final double INTERACT_TO_MOVEMENT = 1f / 2f;
    //
    private final InteractionModel interact = new InteractionModel();
    private final MovementModel movement = new MovementModel();

    public Task nextTask(Bot bot) {
        Task task;
        if (Math.random() < INTERACT_TO_MOVEMENT) {
            // Interact
            task = interact.newInteractTask(bot);
        } else {
            // Movement
            Vector3i newLocation = movement.newTargetLocation(bot);
            task = new WalkTask(bot, newLocation);
        }

        if (task != null) {
            bot.getLogger().info("Activating: " + task.getShortName());
        }

        return task;
    }
}
