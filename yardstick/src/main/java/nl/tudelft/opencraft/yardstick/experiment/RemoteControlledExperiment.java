package nl.tudelft.opencraft.yardstick.experiment;

import static io.javalin.apibuilder.ApiBuilder.get;
import static io.javalin.apibuilder.ApiBuilder.path;
import static io.javalin.apibuilder.ApiBuilder.post;

import com.github.steveice10.mc.auth.exception.request.RequestException;
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
                        path("add", () -> post(this::addAuthPlayer));
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
        createBotAndReplyToClient(context, null);
    }

    private void addAuthPlayer(Context context) {
        Validator<AddPlayerRequest> validator = context.bodyValidator(AddPlayerRequest.class);
        AddPlayerRequest request = validator.get();
        createBotAndReplyToClient(context, request);
    }

    private void createBotAndReplyToClient(Context context, AddPlayerRequest request) {
        try {
            Bot bot;
            if (request != null) {
                bot = createBot(request.getUsername(), request.getPassword());
            } else {
                bot = createBot();
            }
            synchronized (bots) {
                bots.put(bot.getName(), bot);
            }
            context.result(bot.getName());
        } catch (ConnectException | RequestException e) {
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

    public static class AddPlayerRequest {
        private String username;
        private String password;

        public String getUsername() {
            return username;
        }

        public void setUsername(String username) {
            this.username = username;
        }

        public String getPassword() {
            return password;
        }

        public void setPassword(String password) {
            this.password = password;
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
