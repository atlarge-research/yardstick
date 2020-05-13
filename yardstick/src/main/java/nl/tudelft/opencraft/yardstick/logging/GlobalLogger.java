/*
 * Copyright 2015 Jerom van der Sar.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package nl.tudelft.opencraft.yardstick.logging;

import java.io.File;
import java.util.logging.Formatter;
import java.util.logging.Level;
import java.util.logging.FileHandler;

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
            throw new IllegalStateException("Global logger has not be set up");
        }

        return logger;
    }
}
