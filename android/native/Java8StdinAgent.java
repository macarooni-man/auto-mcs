import java.io.FileDescriptor;
import java.io.FileInputStream;
import java.io.FilterInputStream;
import java.lang.instrument.Instrumentation;
import java.lang.reflect.Field;

/**
 * Rebinds System.in to an independent duplicate of the Android hosting pipe.
 * Legacy Java 8 initialization may close fd 0 and redirect it to /dev/null.
 * Compiled with --release 8; used only by auto-mcs Android Java 8 launches.
 */
public final class Java8StdinAgent {
    public static void premain(String descriptor, Instrumentation instrumentation) throws Exception {
        FileDescriptor handle = new FileDescriptor();
        Field number = FileDescriptor.class.getDeclaredField("fd");
        number.setAccessible(true);
        number.setInt(handle, Integer.parseInt(descriptor));

        System.setIn(new FilterInputStream(new FileInputStream(handle)) {
            @Override
            public void close() {
                // Preserve console commands even if a component closes System.in.
            }
        });
    }
}
