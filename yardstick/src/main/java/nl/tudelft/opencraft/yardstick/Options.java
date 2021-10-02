/*
 * Yardstick: A Benchmark for Minecraft-like Services
 * Copyright (C) 2020 AtLarge Research
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

package nl.tudelft.opencraft.yardstick;

import com.beust.jcommander.DynamicParameter;
import com.beust.jcommander.IStringConverter;
import com.beust.jcommander.Parameter;
import com.google.common.base.Joiner;
import com.moandjiezana.toml.Toml;
import java.io.File;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

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

    /**
     * Minecraft-like service
     */
    @Parameter(names = {"--host", "-h"}, description = "The host of the Minecraft server")
    public String host = "127.0.0.1";

    @Parameter(names = {"--port", "-p"}, description = "The port of the Minecraft server")
    public int port = 25565;

    @Parameter(names = {"--architecture"}, description = "The game architecture. singleserver or serverless.")
    public String architecture = "singleserver";

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
        this.host = toml.getString("game.host", this.host);
        this.port = toml.getLong("game.port", (long) this.port).intValue();
        this.architecture = toml.getString("game.architecture");
        this.experiment = toml.getLong("experiment.id", (long) this.experiment).intValue();
        this.experimentParams = toml.getTable("experiment.params").toMap().entrySet()
                .stream()
                .collect(Collectors.toMap(Map.Entry::getKey,
                        e -> e.getValue().toString()));
        this.prometheusHost = toml.getString("pushgateway.host", this.prometheusHost);
        this.prometheusPort = toml.getLong("pushgateway.port", (long) this.prometheusPort).intValue();
        this.start = toml.contains("timing.start") ? new DateConverter().convert(toml.getString("timing.start")) : this.start;
    }

    @Override
    public String toString() {
        return "Options{" + "help=" + help +
                ", dumpWorkload=" + dumpWorkload +
                ", host='" + host + '\'' +
                ", port=" + port +
                ", architecture='" + architecture + '\'' +
                ", experiment=" + experiment +
                ", experimentParams=" + Joiner.on(",").withKeyValueSeparator(":").join(experimentParams) +
                ", prometheusHost='" + prometheusHost + '\'' +
                ", prometheusPort=" + prometheusPort +
                ", start=" + start +
                ", csvDump=" + csvDump +
                ", inFile='" + inFile + '\'' +
                ", outFile='" + outFile + '\'' +
                '}';
    }
}
