package nl.tudelft.vmdumper;

import java.io.IOException;

public class Profiler implements Runnable {

    private static final long DUMP_INTERVAL_MS = 5000;
    //
    private ThreadGroup rootGroup;
    private final FileDump file;

    public Profiler() {
        // http://stackoverflow.com/questions/1323408/get-a-list-of-all-threads-currently-running-in-java/3018672#3018672

        rootGroup = Thread.currentThread().getThreadGroup();
        ThreadGroup parentGroup;
        while ((parentGroup = rootGroup.getParent()) != null) {
            rootGroup = parentGroup;
        }

        file = new FileDump("vmdumper.csv");

        try {
            file.open();
        } catch (IOException ex) {
            throw new RuntimeException("Could not open VMDumper dump file", ex);
        }
    }

    @Override
    public void run() {

        long time = System.currentTimeMillis();

        while (true) {
            dump();

            long newTime = System.currentTimeMillis();
            long sleep = time + DUMP_INTERVAL_MS - newTime;
            if (sleep > 0) {
                try {
                    Thread.sleep(sleep);
                } catch (InterruptedException ex) {
                }
            }
            time += DUMP_INTERVAL_MS;
        }

    }

    private void dump() {
        String key = String.valueOf(System.currentTimeMillis());

        for (Thread thread : getAllThreads()) {
            if (thread == null) {
                continue;
            }
            dumpThread(key, thread);
        }

        file.flush();
    }

    private void dumpThread(String key, Thread thread) {
        file.dump(
                key,
                thread.getName(),
                thread.getId(),
                thread.getPriority(),
                thread.isDaemon(),
                thread.getState()
        );
    }

    private Thread[] getAllThreads() {
        Thread[] threads = new Thread[rootGroup.activeCount()];
        while (rootGroup.enumerate(threads, true) == threads.length) {
            threads = new Thread[threads.length * 2];
        }
        return threads;
    }

}
