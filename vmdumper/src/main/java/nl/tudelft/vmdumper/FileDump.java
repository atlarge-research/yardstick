package nl.tudelft.vmdumper;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;

public class FileDump {

    private final File file;
    private PrintWriter writer;

    public FileDump(String filename) {
        this.file = new File(filename);
    }

    public void open() throws IOException {
        writer = new PrintWriter(new FileWriter(file, true));
    }

    public void dump(Object... values) {
        StringBuilder sb = new StringBuilder();

        sb.append(values[0]);
        for (int i = 1; i < values.length; i++) {
            sb.append(',').append(values[i]);
        }

        writer.println(sb.toString());
        writer.flush();
    }

    public void flush() {
        writer.flush();
    }

    public void close() {
        writer.close();
    }

}
