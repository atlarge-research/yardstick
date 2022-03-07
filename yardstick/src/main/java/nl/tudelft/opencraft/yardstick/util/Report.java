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

package nl.tudelft.opencraft.yardstick.util;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Represents a sealable report of key-value pairs. Once the report is sealed,
 * it can no longer be altered.
 */
public class Report {

    private final String title;
    private final Map<String, Entry> report = new LinkedHashMap<>();
    private boolean sealed = false;

    /**
     * Creates a new report.
     *
     * @param title the report title.
     */
    public Report(String title) {
        this.title = title;
    }

    /**
     * Puts a new key-value pair in the report.
     *
     * @param id    The key of the key-value pair.
     * @param name  The meaning of the key-value pair, in human readable form.
     * @param value The value of the key-value pair.
     */
    public void put(String id, String name, Object value) {
        if (sealed) {
            throw new IllegalStateException("Can not add report entry: Report is sealed!");
        }

        report.put(id, new Entry(name, value.toString()));
    }

    /**
     * Seals the report. Once the report is sealed, it can no longer be altered.
     */
    public void seal() {
        sealed = true;
    }

    /**
     * Returns the report in human-readable form.
     *
     * @return the report String.
     */
    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("Report - ").append(title).append('\n');
        for (String id : report.keySet()) {
            Entry e = report.get(id);
            sb.append("  > ").append(e.getName()).append(": ").append(e.getValue()).append('\n');
        }

        return sb.toString();
    }

    /**
     * Represents an entry of the report.
     */
    public static final class Entry {

        private final String name;
        private final String value;

        /**
         * Creates a new report entry.
         *
         * @param name  the name of the entry.
         * @param value the value of the entry.
         */
        public Entry(String name, String value) {
            this.name = name;
            this.value = value;
        }

        public String getName() {
            return name;
        }

        public String getValue() {
            return value;
        }
    }
}
