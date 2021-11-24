package nl.tudelft.opencraft.yardstick.experiment;

import com.typesafe.config.Config;

public class Experiment12LatencyAndWalkAround extends Experiment {

    private Experiment11Latency latencyExperiment;
    private Experiment8BoxWalkAround walkExperiment;

    public Experiment12LatencyAndWalkAround(int nodeID, String address, Config config) {
        super(12, nodeID, address, config, "latency and walk experiment");
        latencyExperiment = new Experiment11Latency(nodeID, address, config);
        walkExperiment = new Experiment8BoxWalkAround(nodeID, address, config);
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
