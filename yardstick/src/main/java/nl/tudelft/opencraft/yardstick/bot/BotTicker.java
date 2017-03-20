package nl.tudelft.opencraft.yardstick.bot;

import java.util.concurrent.atomic.AtomicBoolean;
import java.util.logging.Logger;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.util.Scheduler;

public class BotTicker implements Runnable {

    private final Logger logger = Logger.getLogger(this.getClass().getName());
    private final Bot bot;
    private final AtomicBoolean running = new AtomicBoolean(false);

    public BotTicker(Bot bot) {
        this.bot = bot;
    }

    public void start() {
        if (!running.compareAndSet(false, true)) {
            throw new IllegalStateException("Already ticking");
        }

        Thread t = new Thread(this);
        t.setName("YSBot Ticker " + bot.getName());
        t.start();
    }

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
                    logger.warning("Task Failure: " + status.getMessage());
                    bot.setTask(null);
                }
            }
            sched.sleepTick();
        }
    }

}
