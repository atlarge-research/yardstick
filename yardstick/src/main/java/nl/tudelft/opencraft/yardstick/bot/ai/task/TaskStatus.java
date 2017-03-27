package nl.tudelft.opencraft.yardstick.bot.ai.task;

public class TaskStatus {

    private final StatusType type;
    private final String message;
    private final Throwable throwable;

    private TaskStatus(StatusType status, String message) {
        this(status, message, null);
    }

    private TaskStatus(StatusType status, String message, Throwable throwable) {
        this.type = status;
        this.message = message;
        this.throwable = throwable;
    }

    public StatusType getType() {
        return type;
    }

    public String getMessage() {
        return message;
    }

    public Throwable getThrowable() {
        return throwable;
    }

    public static TaskStatus forFailure(String message) {
        return new TaskStatus(StatusType.FAILURE, message);
    }

    public static TaskStatus forFailure(String message, Throwable throwable) {
        return new TaskStatus(StatusType.FAILURE, message, throwable);
    }

    public static TaskStatus forSuccess() {
        return new TaskStatus(StatusType.SUCCESS, "Success!");
    }

    public static TaskStatus forInProgress() {
        return new TaskStatus(StatusType.IN_PROGRESS, "In progress.");
    }

    public static enum StatusType {
        IN_PROGRESS,
        SUCCESS,
        FAILURE;
    }
}
