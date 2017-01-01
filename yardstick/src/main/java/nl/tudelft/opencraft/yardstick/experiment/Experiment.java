package nl.tudelft.opencraft.yardstick.experiment;

import nl.tudelft.opencraft.yardstick.Options;
import nl.tudelft.opencraft.yardstick.Report;

public abstract class Experiment {

    protected final Options opts;

    public Experiment(Options opts) {
        this.opts = opts;
    }
    
    public abstract String getDescription();

    public abstract void before();

    public abstract Report after();

    public abstract void tick(long tick);

    public abstract boolean isDone();

}
