package nl.tudelft.opencraft.yardstick.bot.ai.task;

import nl.tudelft.opencraft.yardstick.bot.Bot;

public class StandExecutor extends AbstractTaskExecutor {
    private int timeout = 1000;
    private final long startTime;


    public StandExecutor(Bot bot) {
        super(bot);
        startTime = System.currentTimeMillis();
    }

    public void setTimeout(int timeout) {
        this.timeout = timeout;
    }

    @Override
    protected TaskStatus onTick() {
        long nowTime = System.currentTimeMillis();
//        logger.info("standing, remaing time=" + (timeout+startTime - nowTime));
        if (nowTime - startTime >= timeout) {
            return TaskStatus.forSuccess();
        } else {
            return TaskStatus.forInProgress();
        }
    }

    @Override
    protected void onStop() {

    }
}
