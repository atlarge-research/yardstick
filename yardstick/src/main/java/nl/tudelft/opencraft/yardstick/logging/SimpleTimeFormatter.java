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

package nl.tudelft.opencraft.yardstick.logging;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.text.SimpleDateFormat;
import java.util.logging.Formatter;
import java.util.logging.LogRecord;

/**
 * A formatter for prefixing log records with a date and time.
 */
public class SimpleTimeFormatter extends Formatter {

    private final SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");

    @Override
    public String format(LogRecord record) {
        StringBuilder builder = new StringBuilder();
        Throwable ex = record.getThrown();

        builder.append("[")
                .append(dateFormat.format(record.getMillis()))
                .append("][")
                .append(record.getLevel().getLocalizedName().toUpperCase())
                .append("]");

        if (!record.getLoggerName().equals(GlobalLogger.getLogger().getName())) {
            String[] parts = record.getLoggerName().split("\\.");
            for (String part : parts) {
                builder.append("[")
                        .append(part)
                        .append("]");
            }
        }

        builder.append(" ")
                .append(formatMessage(record))
                .append('\n');

        if (ex != null) {
            StringWriter writer = new StringWriter();
            ex.printStackTrace(new PrintWriter(writer));
            builder.append(writer);
        }

        return builder.toString();
    }
}
