package nl.tudelft.opencraft.yardstick.bot;

import java.util.concurrent.atomic.AtomicBoolean;
import nl.tudelft.opencraft.yardstick.util.Scheduler;

public class BotTicker implements Runnable {

    private final Bot bot;
    private final AtomicBoolean running = new AtomicBoolean(true);

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
            sched.sleepTick();
        }
    }

}
