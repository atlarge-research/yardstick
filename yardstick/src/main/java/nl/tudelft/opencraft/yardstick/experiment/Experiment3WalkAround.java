package nl.tudelft.opencraft.yardstick.experiment;

import nl.tudelft.opencraft.yardstick.Options;
import nl.tudelft.opencraft.yardstick.Report;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import org.spacehq.mc.protocol.MinecraftProtocol;

public class Experiment3WalkAround extends Experiment {

    private Bot bot;
    
    public Experiment3WalkAround(Options opts) {
        super(3, "A simple test demonstrating A* movement", opts);
    }

    @Override
    protected void before() {
        this.bot = new Bot(new MinecraftProtocol("YSBot-1"));
        bot.connect(options.host, options.port);
    }

    @Override
    protected void tick() {
    }

    @Override
    protected boolean isDone() {
        return false;
    }

    @Override
    protected void after() {
        bot.disconnect("disconnect");
    }

    @Override
    public Report report() {
        return new Report("Walk Around");
    }

}
