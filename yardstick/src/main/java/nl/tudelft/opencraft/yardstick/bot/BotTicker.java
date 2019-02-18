package nl.tudelft.opencraft.yardstick.bot;

import java.util.concurrent.atomic.AtomicBoolean;
import java.util.logging.Level;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;
import nl.tudelft.opencraft.yardstick.util.Scheduler;

/**
 * A runnable ticker for executing bot tasks for bots. The BotTicker
 * automatically executes the bot's current task.
 */
public class BotTicker implements Runnable {

    private final SubLogger logger;
    private final Bot bot;
    private final AtomicBoolean running = new AtomicBoolean(false);

    /**
     * Creates a new BotTicker.
     *
     * @param bot the bot.
     */
    public BotTicker(Bot bot) {
        this.bot = bot;
        this.logger = bot.getLogger().newSubLogger("BotTicker");
    }

    /**
     * Starts the BotTicker. The ticker starts in a new thread, which can be
     * stopped with {@link #stop()}.
     */
    public void start() {
        if (!running.compareAndSet(false, true)) {
            throw new IllegalStateException("Already ticking");
        }

        Thread t = new Thread(this);
        t.setName("YSBot Ticker " + bot.getName());
        t.start();
    }

    /**
     * Stops the BotTicker.
     */
    public void stop() {
        running.set(false);
    }

    @Override
    public void run() {
        Scheduler sched = new Scheduler(50); // 50ms per tick
        sched.start();

        while (running.get()) {
            if (bot.getTask() != null
                    && bot.getTask().getStatus().getType() == TaskStatus.StatusType.IN_PROGRESS) {
                TaskStatus status = bot.getTask().tick();
                if (status.getType() == TaskStatus.StatusType.FAILURE) {

                    if (status.getThrowable() != null) {
                        logger.log(Level.WARNING, "Task Failure: " + status.getMessage(), status.getThrowable());
                    } else {
                        logger.warning("Task Failure: " + status.getMessage());
                    }

                    bot.setTask(null);
                }
            }
            sched.sleepTick();
        }
    }

}
