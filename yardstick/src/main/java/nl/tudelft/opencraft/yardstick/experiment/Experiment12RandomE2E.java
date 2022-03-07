package nl.tudelft.opencraft.yardstick.experiment;

import java.io.FileWriter;
import java.util.UUID;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.model.RandomModel;

public class Experiment12RandomE2E extends AbstractModelExperiment {
    public static FileWriter fw;
    private boolean GMjoined;
    private String GMuser;
    public static long GMStartTime;
    public static String GMCommand;

    public Experiment12RandomE2E() {
        super(12, "Bots move around randomly with one GM; log E2E latency", new RandomModel());
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

    protected Bot createBot() {
        if (!GMjoined && GMuser != null) {
            GMjoined = true;
            return newBot(GMuser);
        } else {
            return newBot(UUID.randomUUID().toString().substring(0, 6));
        }
    }
}
