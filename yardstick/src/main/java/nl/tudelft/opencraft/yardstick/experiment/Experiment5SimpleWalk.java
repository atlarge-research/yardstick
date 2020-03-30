package nl.tudelft.opencraft.yardstick.experiment;

import nl.tudelft.opencraft.yardstick.model.SimpleMovementModel;

public class Experiment5SimpleWalk extends AbstractModelExperiment {

    public Experiment5SimpleWalk() {
        super(5, "Bots move around randomly. Based on a movement model for Half Life 2", new SimpleMovementModel());
    }

}
