package nl.tudelft.opencraft.yardstick;

import java.io.File;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

import com.beust.jcommander.DynamicParameter;
import com.beust.jcommander.IStringConverter;
import com.beust.jcommander.Parameter;
import com.moandjiezana.toml.Toml;

/**
 * Represents command line options for the emulator.
 */
public class Options {

    @Parameter(names = {"--help"}, help = true, description = "Shows help")
    public boolean help;

    /**
     * Logging
     */
    @Parameter(names = {"--dump-workload", "-d"}, description = "Indicates whether to dump the workload traces to the 'workload' folder")
    public boolean dumpWorkload;
    @Parameter(names = {"--dump-message-contents"}, description = "Only works in combination with '--dump-workload'. Additionally dumps the contents of every packet.")
    public boolean dumpMessageContents = false;

    /**
     * Minecraft-like service
     */
    @Parameter(names = {"--host", "-h"}, description = "The host of the Minecraft server")
    public String host = "3.123.232.247";
    //public String host = "127.0.0.1";

    @Parameter(names = {"--port", "-p"}, description = "The port of the Minecraft server")
    public int port = 25565;

    /**
     * Experiment
     */
    @Parameter(names = {"--experiment", "-e"}, description = "The experiment ID")
    public int experiment = -1;

    @DynamicParameter(names = "-E", description = "The experiment parameters. Differs per experiment")
    public Map<String, String> experimentParams = new HashMap<>();

    /**
     * Prometheus pushgateway
     */
    @Parameter(names = {"--prometheus-host", "-ph"}, description = "The host of the Prometheus server")
    public String prometheusHost;

    @Parameter(names = {"--prometheus-port", "-pp"}, description = "The port of the Prometheus server")
    public int prometheusPort = 9091;

    /**
     * Timing
     */
    @Parameter(names = {"--start", "-s"}, converter = DateConverter.class, description = "The start time of the experiment - HH:mm[:ss]")
    public LocalTime start;

    /**
     * CSV dumps
     */
    @Parameter(names = {"--csvdump", "-cd"}, description = "Convert a workload file to CSV format")
    public boolean csvDump;

    @Parameter(names = "--input", description = "An input file to read from. To be used with --csvdump")
    public String inFile;

    @Parameter(names = "--output", description = "An output file to write to. To be used with --csvdump")
    public String outFile;

    /**
     * A converter for parsing a String to a LocalTime.
     */
    public static class DateConverter implements IStringConverter<LocalTime> {

        public static DateTimeFormatter FORMATTER = DateTimeFormatter.ISO_LOCAL_TIME;
        //public static DateFormat FORMAT = new SimpleDateFormat("HH:mm:ss");

        @Override
        public LocalTime convert(String string) {
            return LocalTime.from(FORMATTER.parse(string));
        }

    }

    public void readTOML(File f) {
        Toml toml = new Toml().read(f);
        this.dumpWorkload = toml.getBoolean("logging.dump-workload", this.dumpWorkload);
        this.dumpMessageContents = toml.getBoolean("logging.dump-message-contents", this.dumpMessageContents);
        this.host = toml.getString("game.host", this.host);
        this.port = toml.getLong("game.port", (long) this.port).intValue();
        this.experiment = toml.getLong("experiment.id", (long) this.experiment).intValue();
        this.experimentParams = toml.getTable("experiment.params").toMap().entrySet()
                .stream()
                .collect(Collectors.toMap(Map.Entry::getKey,
                        e -> e.getValue().toString()));
        this.prometheusHost = toml.getString("pushgateway.host", this.prometheusHost);
        this.prometheusPort = toml.getLong("pushgateway.port", (long) this.prometheusPort).intValue();
        this.start = toml.contains("timing.start") ? new DateConverter().convert(toml.getString("timing.start")) : this.start;
    }

}
