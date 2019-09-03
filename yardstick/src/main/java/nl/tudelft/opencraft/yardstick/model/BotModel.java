package nl.tudelft.opencraft.yardstick.model;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.playerbehavior.Task;

/**
 * Represents an interaction model of a {@link Bot}.
 */
public interface BotModel {

    /**
     * Generates a new Task for the Bot to execute.
     *
     * @param bot the bot.
     * @return the task.
     */
    Task newTask(Bot bot);

}
