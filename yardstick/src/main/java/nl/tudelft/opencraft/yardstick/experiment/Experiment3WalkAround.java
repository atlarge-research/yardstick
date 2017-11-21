package nl.tudelft.opencraft.yardstick.experiment;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.Task;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTask;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class Experiment3WalkAround extends Experiment {

    private Bot bot;
    private final MovementModel movement = new MovementModel();

    public Experiment3WalkAround() {
        super(3, "A simple test demonstrating A* movement.");
    }

    @Override
    protected void before() {
        this.bot = newBot("YSBot-1");
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
        Task t = bot.getTask();

        if (t == null || t.getStatus().getType() != TaskStatus.StatusType.IN_PROGRESS) {
            Vector3i newLocation = movement.newTargetLocation(bot);
            logger.info(String.format("Setting task for bot to walk to %s", newLocation));
            bot.setTask(new WalkTask(bot, newLocation));
        }
    }

    @Override
    protected boolean isDone() {
        return false;
    }

    @Override
    protected void after() {
        bot.disconnect("disconnect");
    }
}
