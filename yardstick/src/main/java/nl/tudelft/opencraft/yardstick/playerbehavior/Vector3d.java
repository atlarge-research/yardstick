package nl.tudelft.opencraft.yardstick.playerbehavior;

/**
 * Represents an immutable 3 dimensional vector of doubles.
 */
public class Vector3d {

    public static final Vector3d ZERO = new Vector3d(0, 0, 0);
    //
    private final double x, y, z;

    public Vector3d(double x, double y, double z) {
        this.x = x;
        this.y = y;
        this.z = z;
    }

    public double getX() {
        return x;
    }

    public double getY() {
        return y;
    }

    public double getZ() {
        return z;
    }

    public Vector3d add(Vector3d a) {
        return new Vector3d(x + a.x, y + a.y, z + a.z);
    }

    public Vector3d add(double x, double y, double z) {
        return new Vector3d(this.x + x, this.y + y, this.z + z);
    }

    public Vector3d subtract(Vector3d a) {
        return new Vector3d(x - a.x, y - a.y, z - a.z);
    }

    public Vector3d multiply(double a) {
        return new Vector3d(x * a, y * a, z * a);
    }

    public Vector3d divide(double a) {
        return new Vector3d(x / a, y / a, z / a);
    }

    public Vector3d floor() {
        return new Vector3d(Math.floor(x), Math.floor(y), Math.floor(z));
    }

    public double length() {
        return Math.sqrt(lengthSquared());
    }

    public double lengthSquared() {
        return x * x + y * y + z * z;
    }

    public double distance(Vector3d a) {
        return Math.sqrt(distanceSquared(a));
    }

    public double distanceSquared(Vector3d a) {
        double dx = x - a.x;
        double dy = y - a.y;
        double dz = z - a.z;

        return dx * dx + dy * dy + dz * dz;
    }

    public Vector3d unit() {
        double length = length();
        return new Vector3d(x / length, y / length, z / length);
    }

    public Vector3i intVector() {
        return new Vector3i((int) Math.floor(x), (int) Math.floor(y), (int) (int) Math.floor(z));
    }

    @Override
    public int hashCode() {
        int hash = 5;
        hash = 17 * hash + (int) (Double.doubleToLongBits(this.x) ^ (Double.doubleToLongBits(this.x) >>> 32));
        hash = 17 * hash + (int) (Double.doubleToLongBits(this.y) ^ (Double.doubleToLongBits(this.y) >>> 32));
        hash = 17 * hash + (int) (Double.doubleToLongBits(this.z) ^ (Double.doubleToLongBits(this.z) >>> 32));
        return hash;
    }

    @Override
    public String toString() {
        return "(" + x + ", " + y + ", " + z + ")";
    }

    @Override
    public boolean equals(Object obj) {
        if (obj == null) {
            return false;
        }

        if (!(obj instanceof Vector3d)) {
            return false;
        }

        Vector3d other = (Vector3d) obj;

        return x == other.x && y == other.y && z == other.z;
    }

}
