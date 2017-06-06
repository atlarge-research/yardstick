package nl.tudelft.opencraft.yardstick.workload;

import java.io.BufferedInputStream;
import java.io.DataInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.zip.GZIPInputStream;
import nl.tudelft.opencraft.yardstick.Yardstick;

public class CsvConverter {

    private static final Logger LOGGER = Yardstick.LOGGER.newSubLogger("CSV Converter");

    private CsvConverter() {
    }

    public static void convertCsv(String inFileName, String outFileName) throws IOException {
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
            FileInputStream fos = new FileInputStream(inFile);
            BufferedInputStream bos = new BufferedInputStream(fos);
            //GZIPInputStream gos = new GZIPInputStream(in);

            in = new DataInputStream(bos);
        } catch (FileNotFoundException ex) {
            LOGGER.log(Level.SEVERE, "Could not read from file: " + inFileName, ex);
            return;
        }

        LOGGER.info("Converting: " + inFileName);
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
                int nameLength = in.readInt();
                if (nameLength > 100) {
                    LOGGER.warning("Long packet name: " + nameLength);
                }
                byte[] name = new byte[nameLength];
                in.readFully(name);
                sb.append(new String(name, StandardCharsets.UTF_8)).append(',');

                // Packet length
                sb.append(in.readLong());

                sb.append('\n');
                out.write(sb.toString());
                packets++;
            }

            LOGGER.info("Converted " + packets + " packets");
        } catch (Exception ex) {
            LOGGER.log(Level.SEVERE, "Could not convert to CSV: " + outFileName, ex);
        } finally {
            try {
                in.close();
            } catch (IOException ex) {
            }
            out.flush();
            out.close();
        }

    }

}
