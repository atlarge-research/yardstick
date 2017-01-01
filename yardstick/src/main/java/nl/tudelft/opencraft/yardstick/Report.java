package nl.tudelft.opencraft.yardstick;

import java.util.LinkedHashMap;
import java.util.Map;

public class Report {

    private final String title;
    private final Map<String, Entry> report = new LinkedHashMap<>();
    private boolean sealed = false;

    public Report(String title) {
        this.title = title;
    }

    public void put(String id, String name, Object value) {
        if (sealed) {
            throw new IllegalStateException("Can not add report entry: Report is sealed!");
        }

        report.put(id, new Entry(name, value.toString()));
    }

    public void seal() {
        sealed = true;
    }

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

    public static final class Entry {

        private final String name;
        private final String value;

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
