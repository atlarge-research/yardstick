package nl.tudelft.opencraft.yardstick.telemetry;

import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.exporter.logging.LoggingMetricExporter;
import io.opentelemetry.exporter.logging.LoggingSpanExporter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.metrics.SdkMeterProvider;
import io.opentelemetry.sdk.metrics.export.MetricReaderFactory;
import io.opentelemetry.sdk.metrics.export.PeriodicMetricReader;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;
import lombok.Getter;

import java.time.Duration;

/**
 * Provides access to the OpenTelemetry API.
 * Code based on example available here:
 * https://github.com/open-telemetry/opentelemetry-java-docs/blob/main/logging/src/main/java/io/opentelemetry/example/logging/ExampleConfiguration.java
 */
public class OpenTelemetrySingleton {

    /**
     * The number of milliseconds between metric exports.
     */
    private static final long METRIC_EXPORT_INTERVAL_MS = 800L;

    @Getter(lazy = true)
    private final OpenTelemetry telemetry = initTelemetry();

    private OpenTelemetry initTelemetry() {
        // Create an instance of PeriodicMetricReaderFactory and configure it
        // to export via the logging exporter
        MetricReaderFactory periodicReaderFactory =
                PeriodicMetricReader.builder(LoggingMetricExporter.create())
                        .setInterval(Duration.ofMillis(METRIC_EXPORT_INTERVAL_MS))
                        .newMetricReaderFactory();

        // This will be used to create instruments
        SdkMeterProvider meterProvider =
                SdkMeterProvider.builder().registerMetricReader(periodicReaderFactory).build();

        // Tracer provider configured to export spans with SimpleSpanProcessor using
        // the logging exporter.
        SdkTracerProvider tracerProvider =
                SdkTracerProvider.builder()
                        .addSpanProcessor(SimpleSpanProcessor.create(LoggingSpanExporter.create()))
                        .build();
        return OpenTelemetrySdk.builder()
                .setMeterProvider(meterProvider)
                .setTracerProvider(tracerProvider)
                .buildAndRegisterGlobal();
    }
}
