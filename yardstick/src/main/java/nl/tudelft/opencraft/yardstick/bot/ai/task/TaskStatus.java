package nl.tudelft.opencraft.yardstick.bot.ai.task;

public class TaskStatus {

    private final StatusType type;
    private final String message;

    private TaskStatus(StatusType status, String message) {
        this.type = status;
        this.message = message;
    }

    public StatusType getType() {
        return type;
    }

    public String getMessage() {
        return message;
    }

    public static TaskStatus forFailure(String message) {
        return new TaskStatus(StatusType.FAILURE, message);
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
