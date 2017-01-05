package nl.tudelft.opencraft.yardstick;

import com.beust.jcommander.DynamicParameter;
import com.beust.jcommander.Parameter;
import java.util.HashMap;
import java.util.Map;

public class Options {

    @Parameter(names = {"--help"}, help = true)
    public boolean help;

    @Parameter(names = {"--experiment", "-e"}, required = true)
    public int experiment;

    @Parameter(names = {"--host", "-h"}, required = true)
    public String host;

    @Parameter(names = {"--port", "-p"}, required = true)
    public int port;

    @DynamicParameter(names = "-E", description = "Experiment parameters.")
    public Map<String, String> experimentParams = new HashMap<>();

}
