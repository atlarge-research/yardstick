package nl.tudelft.vmdumper;

import java.lang.instrument.Instrumentation;

public class Agent {

    public static void agentmain(final String args, final Instrumentation instrumentation) {
        premain(args, instrumentation);
    }

    /**
     * Start the profiler
     *
     * @param args Profiler arguments
     * @param instrumentation Instrumentation agent
     */
    public static void premain(final String args, final Instrumentation instrumentation) {

        Thread profiler = new Thread(new Profiler());
        profiler.setName("VMDumper Profiler");
        profiler.setDaemon(false);
        profiler.start();

    }

}
