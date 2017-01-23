/*
 Copyright (c) 2013, DarkStorm (darkstorm@evilminecraft.net)
 All rights reserved.

 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions are met: 

 1. Redistributions of source code must retain the above copyright notice, this
 list of conditions and the following disclaimer. 
 2. Redistributions in binary form must reproduce the above copyright notice,
 this list of conditions and the following disclaimer in the documentation
 and/or other materials provided with the distribution. 

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
 ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
package nl.tudelft.opencraft.yardstick.bot.ai;

public interface Task {

    /**
     * Returns true if the precondition to activate it is met.
     */
    public boolean isPreconditionMet();

    /**
     * Starts the task.
     */
    public boolean start(String... options);

    /**
     * Stops the task. This is called either when it becomes inactive or it is told to stop.
     */
    public void stop();

    /**
     * Called every game tick that it is active.
     */
    public void run();

    /**
     * Returns true as long as the task can continue to tick.
     */
    public boolean isActive();

    /**
     * Returns the priority of the task. This only pertains to tasks that are exclusive. If multiple exclusive tasks are active, the task with the highest priority will take precedence. If the there
     * is more than one task of highest priority, the task that was started first will take precedence.
     *
     * @see Task#isExclusive()
     */
    public TaskPriority getPriority();

    /**
     * Returns true if all other tasks should be put on hold while this task is active.
     *
     * @see Task#getPriority()
     */
    public boolean isExclusive();

    /**
     * Returns true if this task ignores other active tasks that are exclusive.
     */
    public boolean ignoresExclusive();

    /**
     * The name of the task (e.g. FollowTask would have the name Follow)
     */
    public String getName();

    /**
     * Describes the options provided to start the task.
     */
    public String getOptionDescription();
}
