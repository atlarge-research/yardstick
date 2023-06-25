package nl.tudelft.opencraft.yardstick.bot.ai.task;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

public class FutureTaskExecutor implements TaskExecutor {

    private final CompletableFuture<? extends TaskExecutor> futureTaskExecutor;

    public FutureTaskExecutor(CompletableFuture<? extends TaskExecutor> futureTaskExecutor) {
        this.futureTaskExecutor = futureTaskExecutor;
    }

    @Override
    public String getShortName() {
        return this.getClass().getSimpleName();
    }

    @Override
    public TaskStatus getStatus() {
        if (futureTaskExecutor.isCancelled()) {
            return TaskStatus.forFailure("task was cancelled");
        } else if (futureTaskExecutor.isCompletedExceptionally()) {
            return TaskStatus.forFailure("task failed");
        } else if (futureTaskExecutor.isDone()) {
            try {
                return futureTaskExecutor.get().getStatus();
            } catch (InterruptedException | ExecutionException e) {
                throw new RuntimeException(e);
            }
        } else {
            return TaskStatus.forInProgress();
        }
    }

    @Override
    public TaskStatus tick() {
        var task = futureTaskExecutor.getNow(null);
        if (task != null) {
            return task.tick();
        }
        return getStatus();
    }

    @Override
    public void stop() {
        var task = futureTaskExecutor.getNow(null);
        if (task != null) {
            task.stop();
        }
        futureTaskExecutor.cancel(false);
    }
}
