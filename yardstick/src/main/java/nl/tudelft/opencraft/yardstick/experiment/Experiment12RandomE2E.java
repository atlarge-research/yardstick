package nl.tudelft.opencraft.yardstick.experiment;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.game.GameArchitecture;
import nl.tudelft.opencraft.yardstick.model.RandomModel;
import nl.tudelft.opencraft.yardstick.statistic.ChatLatencyListener;

import java.io.FileWriter;
import java.time.Duration;
import java.util.UUID;

public class Experiment12RandomE2E extends AbstractModelExperiment {
    public static FileWriter fw;
    private boolean GMjoined;
    private String GMuser;
    public static long GMStartTime;
    public static String GMCommand;

    public Experiment12RandomE2E(int nodeID, GameArchitecture game, Duration duration) {
        super(12, nodeID, game, duration, "Bots move around randomly with one GM; log E2E latency", new RandomModel());
        try {
            fw = new FileWriter("event.log");
        } catch (Exception e) {
            e.printStackTrace();
        }
        GMuser = options.experimentParams.get("gmuser");
        GMCommand = options.experimentParams.getOrDefault("gmcommand", "random");
        RandomModel randomModel = (RandomModel) getModel();
        randomModel.setMovementDiameter(0);
        randomModel.setGMUser(GMuser);
        randomModel.setGMInterval(Long.parseLong(options.experimentParams.getOrDefault("gminterval", "10")));
    }

    @Override
    protected Bot createBot() {
        if (!GMjoined && GMuser != null) {
            GMjoined = true;
            Bot bot = newBot(GMuser);
            bot.addListener(new ChatLatencyListener());
            return bot;
        } else {
            Bot bot = newBot(UUID.randomUUID().toString().substring(0, 6));
            bot.addListener(new ChatLatencyListener());
            return bot;
        }
    }
}
