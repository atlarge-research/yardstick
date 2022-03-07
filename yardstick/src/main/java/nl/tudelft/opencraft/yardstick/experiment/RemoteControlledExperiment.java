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

package nl.tudelft.opencraft.yardstick.experiment;

import static io.javalin.apibuilder.ApiBuilder.get;
import static io.javalin.apibuilder.ApiBuilder.path;
import static io.javalin.apibuilder.ApiBuilder.post;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import io.javalin.Javalin;
import io.javalin.core.validation.Validator;
import io.javalin.http.Context;
import io.javalin.plugin.json.JavalinJson;
import java.util.HashMap;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.Task;
import nl.tudelft.opencraft.yardstick.bot.world.ConnectException;

public class RemoteControlledExperiment extends Experiment {

    private final HashMap<String, Bot> bots = new HashMap<>();
    private final Gson gson = new GsonBuilder().create();
    private boolean done = false;

    /**
     * Creates a new experiment.
     */
    public RemoteControlledExperiment() {
        super(7, "Experiment Controlled Through REST API.");
    }

    @Override
    protected void before() {
        Javalin app = Javalin.create(config -> {
            config.defaultContentType = "application/json";
        }).routes(() -> {
            path("player",
                    () -> {
                        path("control", () -> {
                            path("add", () -> get(this::addPlayer));
                            path("list", () -> get(this::playerList));

                        });
                        path("behavior", () -> {
                            path("command", () -> post(this::giveCommands));
                            path("status", () -> post(this::getStatus));
                        });
                    });
            path("stop",
                    () -> get(ctx -> {
                        this.done = true;
                        ctx.result("done");
                    }));
        }).start(7000);
        app.get("/", ctx -> ctx.result("Hello World"));
    }

    private void getStatus(Context context) {
        Validator<PlayerStatusRequest> validator = context.bodyValidator(PlayerStatusRequest.class);
        PlayerStatusRequest rq = validator.getOrNull();
        synchronized (bots) {
            if (rq == null) {
                logger.warning(String.format("Received invalid PlayerStatusRequest: %s", context.body()));
                context.status(400);
            } else if (bots.containsKey(rq.getPlayerName())) {
                context.result(JavalinJson.toJson(bots.get(rq.getPlayerName())));
            } else {
                // TODO let client know bot is unknown.
                context.status(400);
            }
        }
    }

    private void giveCommands(Context context) {
        Validator<RemoteCommand> validator = context.bodyValidator(RemoteCommand.class);
        RemoteCommand command = validator.get();
        synchronized (bots) {
            if (bots.containsKey(command.getPlayerName())) {
                final Bot bot = bots.get(command.getPlayerName());
                bot.setTaskExecutor(command.task.toExecutor(bot));
            }
        }
    }

    private void playerList(Context context) {
        synchronized (bots) {
            context.result(JavalinJson.toJson(bots.keySet().toArray()));
        }
    }

    private void addPlayer(Context context) {
        try {
            Bot bot = createBot();
            synchronized (bots) {
                bots.put(bot.getName(), bot);
            }
            context.result(bot.getName());
        } catch (ConnectException e) {
            e.printStackTrace();
        }
    }

    @Override
    protected void tick() {

    }

    @Override
    protected boolean isDone() {
        return this.done;
    }

    @Override
    protected void after() {
    }

    public static class RemoteCommand {
        private String playerName;
        private Task task;

        public String getPlayerName() {
            return playerName;
        }

        public void setPlayerName(String playerName) {
            this.playerName = playerName;
        }

        public Task getTask() {
            return task;
        }

        public void setTask(Task task) {
            this.task = task;
        }
    }

    public static class PlayerStatusRequest {
        private String playerName;

        public String getPlayerName() {
            return playerName;
        }

        public void setPlayerName(String playerName) {
            this.playerName = playerName;
        }
    }
}
