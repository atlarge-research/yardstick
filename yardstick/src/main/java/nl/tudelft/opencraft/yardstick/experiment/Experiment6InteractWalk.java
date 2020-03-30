package nl.tudelft.opencraft.yardstick.experiment;

import nl.tudelft.opencraft.yardstick.model.MoveInteractModel;

public class Experiment6InteractWalk extends AbstractModelExperiment {

    public Experiment6InteractWalk() {
        super(6, "Bots move around randomly and have a chance to break or place blocks", new MoveInteractModel());
    }

}
