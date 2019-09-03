package nl.tudelft.opencraft.yardstick.playerbehavior;

public class RunJSBehavior {

    public void test() {
        Context context = Context.newBuilder("js").allowHostAccess(true).build();
        context.eval("js", jsSourceCode);
    }
}
