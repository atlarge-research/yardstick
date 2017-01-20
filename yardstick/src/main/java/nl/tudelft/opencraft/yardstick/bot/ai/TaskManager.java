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

import nl.tudelft.opencraft.yardstick.bot.ai.activity.Activity;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import nl.tudelft.opencraft.yardstick.bot.Bot;

public class TaskManager {

    private final Bot bot;
    private final Map<Class<? extends Task>, Task> tasks = new HashMap<>();
    private final Map<Task, BigInteger> startTimes = new HashMap<>();
    //
    private Activity activity;

    public TaskManager(Bot bot) {
        this.bot = bot;
    }
    
    public synchronized Activity getActivity() {
        return activity;
    }

    public synchronized boolean register(Task task) {
        if (task == null) {
            return false;
        }
        if (tasks.get(task.getClass()) != null) {
            return false;
        }
        tasks.put(task.getClass(), task);
        return true;
    }

    public synchronized boolean unregister(Task task) {
        if (task == null) {
            return false;
        }
        return TaskManager.this.unregister(task.getClass());
    }

    public synchronized boolean unregister(Class<? extends Task> taskClass) {
        if (taskClass == null) {
            return false;
        }
        Task task = tasks.remove(taskClass);
        if (task != null) {
            if (task.isActive()) {
                task.stop();
            }
            startTimes.remove(task);
        }
        return task != null;
    }

    public synchronized void update() {
        List<Task> exclusiveIgnoringTasks = new ArrayList<>();
        Task highestExclusiveTask = null;
        int highestPriority = -1;
        BigInteger highestStartTime = null;
        for (Task task : tasks.values()) {
            boolean active = task.isActive();
            boolean hasStartTime = startTimes.containsKey(task);
            if (hasStartTime && !active) {
                startTimes.remove(task);
            } else if (!hasStartTime && active) {
                startTimes.put(task,
                        BigInteger.valueOf(System.currentTimeMillis()));
            }

            if (!active && task.isPreconditionMet()) {
                if (task.start()) {
                    startTimes.put(task,
                            BigInteger.valueOf(System.currentTimeMillis()));
                } else {
                    task.stop();
                }
            }
            if (task.isExclusive() && active) {
                int taskPriority = task.getPriority().ordinal();
                BigInteger taskStartTime = startTimes.get(task);
                if (highestExclusiveTask == null
                        || taskPriority > highestPriority
                        || (taskPriority == highestPriority && taskStartTime
                        .compareTo(highestStartTime) < 0)) {
                    highestExclusiveTask = task;
                    highestPriority = taskPriority;
                    highestStartTime = taskStartTime;
                }
            }
            if (task.ignoresExclusive()) {
                exclusiveIgnoringTasks.add(task);
            }
        }

        if (activity != null || highestExclusiveTask != null) {
            if (activity == null) {
                highestExclusiveTask.run();
                if (!highestExclusiveTask.isActive()) {
                    highestExclusiveTask.stop();
                    startTimes.remove(highestExclusiveTask);
                }
            }
            for (Task task : exclusiveIgnoringTasks) {
                if (task.isActive()) {
                    task.run();
                    if (!task.isActive()) {
                        task.stop();
                        startTimes.remove(task);
                    }
                }
            }
            return;
        }

        for (Task task : tasks.values()) {
            if (task.isActive()) {
                task.run();
                if (!task.isActive()) {
                    task.stop();
                    startTimes.remove(task);
                }
            }
        }
    }

    public synchronized void stopAll() {
        for (Task task : tasks.values()) {
            if (task.isActive()) {
                task.stop();
            }
        }
    }

    public synchronized <T extends Task> T getTaskFor(Class<T> taskClass) {
        if (taskClass == null) {
            return null;
        }
        return (T) tasks.get(taskClass);
    }

    public List<Task> getRegisteredTasks() {
        return new ArrayList<>(tasks.values());
    }
}
