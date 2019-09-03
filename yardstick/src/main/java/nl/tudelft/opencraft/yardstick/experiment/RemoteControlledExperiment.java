package nl.tudelft.opencraft.yardstick.experiment;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import io.javalin.Javalin;
import io.javalin.http.Context;
import io.javalin.plugin.json.JavalinJson;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.ConnectException;

import java.util.ArrayList;
import java.util.List;

import static io.javalin.apibuilder.ApiBuilder.get;
import static io.javalin.apibuilder.ApiBuilder.path;

public class RemoteControlledExperiment extends Experiment {

    private final List<Bot> bots = new ArrayList<>();
    private final Gson gson = new GsonBuilder().create();
    private boolean done = false;

    /**
     * Creates a new experiment.
     *
     */
    public RemoteControlledExperiment() {
        super(7, "Experiment Controlled Through REST API.");
    }

    @Override
    protected void before() {
        Javalin app = Javalin.create(config -> {
            config.defaultContentType = "application/json";
        }).routes(() -> {
            path("players",
                    () -> {
                        path("add", () -> get(this::addPlayer));
                        path("list", () -> get(this::playerList));

                    });
            path("stop",
                    () -> get(ctx -> {
                        this.done = true;
                        ctx.result("done");
                    }));
        }).start(7000);
        app.get("/", ctx -> ctx.result("Hello World"));
    }

    private void playerList(Context context) {
        synchronized (bots) {
            context.result(JavalinJson.toJson(bots.stream().map(Bot::getName).toArray()));
        }
    }

    private void addPlayer(Context context) {
        try {
            Bot bot = createBot();
            synchronized (bots) {
                bots.add(bot);
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
}
