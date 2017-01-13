package nl.tudelft.opencraft.yardstick;

import com.beust.jcommander.DynamicParameter;
import com.beust.jcommander.IStringConverter;
import com.beust.jcommander.Parameter;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
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

    @Parameter(names = {"--start", "-s"}, converter = DateConverter.class)
    public LocalTime start;

    @DynamicParameter(names = "-E", description = "Experiment parameters.")
    public Map<String, String> experimentParams = new HashMap<>();

    public static class DateConverter implements IStringConverter<LocalTime> {

        public static DateTimeFormatter FORMATTER = DateTimeFormatter.ISO_LOCAL_TIME;
        //public static DateFormat FORMAT = new SimpleDateFormat("HH:mm:ss");

        @Override
        public LocalTime convert(String string) {
            return LocalTime.from(FORMATTER.parse(string));
        }

    }

}
