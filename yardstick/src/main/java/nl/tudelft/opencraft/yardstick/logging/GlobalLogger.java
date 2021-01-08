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

import java.io.File;
import java.util.logging.Formatter;
import java.util.logging.Level;

/**
 * Represents a logger for logging data.
 */
public class GlobalLogger extends SubLogger {

    private static GlobalLogger logger;

    private GlobalLogger(String name) {
        super(name);
    }

    public void setupFileLogging(String file) {
        setupFileLogging(new SimpleTimeFormatter(), file);
    }

    public void setupFileLogging(Formatter formatter, File file) {
        logger.addHandler(new SimpleFileHandler(formatter, file));
    }

    public void setupFileLogging(Formatter formatter, String file) {
        logger.addHandler(new SimpleFileHandler(formatter, file));
    }

    public void setupConsoleLogging() {
        setupConsoleLogging(new SimpleTimeFormatter());
    }

    public void setupConsoleLogging(Formatter formatter) {
        logger.addHandler(new SimpleConsoleHandler(formatter));
    }

    public void handleException(Throwable ex) {
        logger.log(Level.SEVERE, "Received uncaught exception!", ex);
        System.exit(1);
    }

    public static GlobalLogger setupGlobalLogger(Class<?> clazz) {
        return setupGlobalLogger(clazz.getSimpleName());
    }

    public static GlobalLogger setupGlobalLogger(String name) {
        if (logger != null) {
            throw new IllegalStateException("Cannot setup global logger twice");
        }

        logger = new GlobalLogger(name);
        logger.setLevel(Level.INFO);

        return logger;
    }

    public static GlobalLogger getLogger() {
        if (logger == null) {
            logger = setupGlobalLogger("Yardstick");
        }
        return logger;
    }
}
