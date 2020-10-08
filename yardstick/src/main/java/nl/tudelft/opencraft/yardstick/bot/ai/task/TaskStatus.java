package nl.tudelft.opencraft.yardstick.bot.ai.task;

/**
 * Represents the status of a task.
 */
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

    /**
     * Returns the type of status.
     *
     * @return the type.
     */
    public StatusType getType() {
        return type;
    }

    /**
     * Returns the message, if any.
     *
     * @return the message.
     */
    public String getMessage() {
        return message;
    }

    /**
     * Returns the failure throwable, if any.
     *
     * @return the throwable.
     */
    public Throwable getThrowable() {
        return throwable;
    }

    /**
     * Creates a new failure status.
     *
     * @param message the failure message.
     * @return the status.
     */
    public static TaskStatus forFailure(String message) {
        return new TaskStatus(StatusType.FAILURE, message);
    }

    /**
     * Creates a new failure status.
     *
     * @param throwable the failure throwable.
     * @return the status.
     */
    public static TaskStatus forFailure(String message, Throwable throwable) {
        return new TaskStatus(StatusType.FAILURE, message, throwable);
    }

    /**
     * Creates a new success status.
     *
     * @return the status.
     */
    public static TaskStatus forSuccess() {
        return new TaskStatus(StatusType.SUCCESS, "Success!");
    }

    /**
     * Creates a new in-progress status.
     *
     * @return the status.
     */
    public static TaskStatus forInProgress() {
        return new TaskStatus(StatusType.IN_PROGRESS, "In progress.");
    }

    /**
     * Represents a type of status.
     */
    public static enum StatusType {
        IN_PROGRESS,
        SUCCESS,
        FAILURE;
    }
}
