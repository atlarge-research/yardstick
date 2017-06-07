package nl.tudelft.opencraft.yardstick.workload;

import java.io.BufferedInputStream;
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
            FileInputStream fos = new FileInputStream(inFile);
            BufferedInputStream bos = new BufferedInputStream(fos);
            //GZIPInputStream gos = new GZIPInputStream(in);

            in = new DataInputStream(bos);
        } catch (FileNotFoundException ex) {
            LOGGER.log(Level.SEVERE, "Could not read from file: " + inFileName, ex);
            return;
        }

        LOGGER.info("Converting: " + inFileName);
        int packets = 0;
        try {
            out.write("timestamp,outgoing,name,length\n");

            while (in.available() > 0) {
                PacketEntry entry = PacketEntry.readFrom(in);
                out.write(entry.toCsv());
                packets++;
            }

            LOGGER.info("Converted " + packets + " packets");
        } catch (Exception ex) {
            LOGGER.log(Level.SEVERE, "Could not convert to CSV: " + outFileName + ". At packet: " + packets, ex);
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
