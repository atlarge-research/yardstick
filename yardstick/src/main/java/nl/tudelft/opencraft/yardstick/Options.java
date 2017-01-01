package nl.tudelft.opencraft.yardstick;

import com.beust.jcommander.Parameter;

public class Options {

    @Parameter(names = {"--help"}, help = true)
    public boolean help;

    @Parameter(names = {"--experiment", "-e"}, required = true)
    public int experiment;

    @Parameter(names = {"--host", "-h"}, required = true)
    public String host;

    @Parameter(names = {"--port", "-p"}, required = true)
    public int port;

}
