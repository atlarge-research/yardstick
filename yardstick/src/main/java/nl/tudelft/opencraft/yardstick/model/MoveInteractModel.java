package nl.tudelft.opencraft.yardstick.model;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;

/**
 * Represents a model which moves and interacts with the environment.
 */
public class MoveInteractModel implements BotModel {

    private static final double INTERACT_TO_MOVEMENT = 1f / 10f;
    //
    private final BotModel interact = new SimpleInteractionModel();
    private final BotModel movement = new SimpleMovementModel();

    @Override
    public TaskExecutor newTask(Bot bot) {
        TaskExecutor taskExecutor;
        if (Math.random() < INTERACT_TO_MOVEMENT) {
            // Interact
            taskExecutor = interact.newTask(bot);
        } else {
            // Movement
            taskExecutor = movement.newTask(bot);
        }

        return taskExecutor;
    }

}
