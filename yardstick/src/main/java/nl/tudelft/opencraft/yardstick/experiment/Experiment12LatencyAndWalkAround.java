package nl.tudelft.opencraft.yardstick.experiment;

import com.typesafe.config.Config;
import nl.tudelft.opencraft.yardstick.game.GameArchitecture;

public class Experiment12LatencyAndWalkAround extends Experiment {

    private final Experiment11Latency latencyExperiment;
    private final Experiment8BoxWalkAround walkExperiment;

    public Experiment12LatencyAndWalkAround(int nodeID, GameArchitecture game, Config config) {
        super(12, nodeID, game, "latency and walk experiment");
        latencyExperiment = new Experiment11Latency(nodeID, game, config);
        walkExperiment = new Experiment8BoxWalkAround(nodeID, game, config);
    }

    @Override
    protected void before() throws InterruptedException {
        latencyExperiment.before();
        walkExperiment.before();
    }

    @Override
    protected void tick() {
        latencyExperiment.tick();
        walkExperiment.tick();
    }

    @Override
    protected boolean isDone() {
        return latencyExperiment.isDone() && walkExperiment.isDone();
    }

    @Override
    protected void after() {
        latencyExperiment.after();
        walkExperiment.after();
    }
}
