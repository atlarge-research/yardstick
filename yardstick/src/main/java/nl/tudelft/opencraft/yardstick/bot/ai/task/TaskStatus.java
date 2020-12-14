/*
 * Yardstick: A Benchmark for Minecraft-like Services
 * Copyright (C) 2020 AtLarge Research
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

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
