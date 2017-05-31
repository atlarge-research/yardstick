package nl.tudelft.opencraft.yardstick.workload;

import java.io.DataInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.logging.Level;
import java.util.logging.Logger;
import nl.tudelft.opencraft.yardstick.Yardstick;

public class CsvConverter {

    private static final Logger LOGGER = Yardstick.LOGGER.newSubLogger("CSV Converter");

    private CsvConverter() {
    }

    public static void convertCsv(String inFileName, String outFileName) {
        File inFile = new File(inFileName);
        File outFile = new File(outFileName);

        if (!inFile.exists() || !inFile.isFile()) {
            LOGGER.severe("File does not exist: " + inFileName);
            return;
        }

        outFile.getParentFile().mkdirs();

        PrintWriter out;
        try {
            out = new PrintWriter(outFile);
        } catch (FileNotFoundException ex) {
            LOGGER.log(Level.SEVERE, "Could not write to file: " + outFileName, ex);
            return;
        }

        DataInputStream in;
        try {
            in = new DataInputStream(new FileInputStream(inFile));
        } catch (FileNotFoundException ex) {
            LOGGER.log(Level.SEVERE, "Could not read from file: " + inFileName, ex);
            return;
        }

        try {
            out.write("timestamp,outgoing,name,length\n");

            int packets = 0;
            while (in.available() > 0) {
                StringBuilder sb = new StringBuilder();

                // Timestamp
                sb.append(in.readLong()).append(',');

                // Incoming/outgoing
                boolean outgoing = in.readByte() == 1;
                sb.append(outgoing).append(',');

                // Packet Name
                String packetName = in.readUTF();
                sb.append(packetName).append(',');

                // Packet length
                sb.append(in.readLong());

                sb.append('\n');
                out.write(sb.toString());
                packets++;
            }

            LOGGER.info("Converted " + packets + " packets");
        } catch (Exception ex) {
            LOGGER.log(Level.SEVERE, "Could not convert to CSV", ex);
            return;
        }

        try {
            in.close();
        } catch (IOException ex) {
        }
        out.flush();
        out.close();
    }

}
