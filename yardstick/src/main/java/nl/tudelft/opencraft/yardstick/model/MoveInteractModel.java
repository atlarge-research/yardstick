package nl.tudelft.opencraft.yardstick.model;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.Task;

/**
 * Represents a model which moves and interacts with the environment.
 */
public class MoveInteractModel implements BotModel {

    private static final double INTERACT_TO_MOVEMENT = 1f / 2f;
    //
    private final BotModel interact = new SimpleInteractionModel();
    private final BotModel movement = new SimpleMovementModel();

    @Override
    public Task newTask(Bot bot) {
        Task task;
        if (Math.random() < INTERACT_TO_MOVEMENT) {
            // Interact
            task = interact.newTask(bot);
        } else {
            // Movement
            task = movement.newTask(bot);
        }

        return task;
    }

}
