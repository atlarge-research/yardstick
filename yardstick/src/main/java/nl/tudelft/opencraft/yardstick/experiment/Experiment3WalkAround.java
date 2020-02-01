package nl.tudelft.opencraft.yardstick.experiment;

import com.github.steveice10.mc.auth.exception.request.RequestException;
import nl.tudelft.opencraft.yardstick.model.SimpleMovementModel;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTaskExecutor;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class Experiment3WalkAround extends Experiment {

    private Bot bot;
    private final SimpleMovementModel movement = new SimpleMovementModel();
    private boolean done = false;

    public Experiment3WalkAround() {
        super(3, "A simple test demonstrating A* movement.");
    }

    @Override
    protected void before() {
        try {
            this.bot = newBot("YSBot-1");
        } catch (RequestException e) {
            logger.severe("Could not connect bot. Stopping experiment.");
            this.done = true;
            return;
        }
        this.bot.connect();

        // TODO: Do something about this
        while (this.bot.getPlayer() == null) {
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                e.printStackTrace();
                return;
            }
        }
        while (this.bot.getPlayer().getLocation() == null) {
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                e.printStackTrace();
                return;
            }
        }
    }

    @Override
    protected void tick() {
        TaskExecutor t = bot.getTaskExecutor();

        if (t == null || t.getStatus().getType() != TaskStatus.StatusType.IN_PROGRESS) {
            Vector3i newLocation = movement.newTargetLocation(bot);
            logger.info(String.format("Setting task for bot to walk to %s", newLocation));
            bot.setTaskExecutor(new WalkTaskExecutor(bot, newLocation));
        }
    }

    @Override
    protected boolean isDone() {
        return done;
    }

    @Override
    protected void after() {
        bot.disconnect("disconnect");
    }
}
