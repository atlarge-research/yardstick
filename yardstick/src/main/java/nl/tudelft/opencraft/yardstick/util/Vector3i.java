package nl.tudelft.opencraft.yardstick.util;

/**
 * Represents an immutable 3 dimensional vector of ints.
 */
public class Vector3i {

    public static final Vector3i ZERO = new Vector3i(0, 0, 0);
    //
    private final int x, y, z;

    public Vector3i(int x, int y, int z) {
        this.x = x;
        this.y = y;
        this.z = z;
    }

    public int getX() {
        return x;
    }

    public int getY() {
        return y;
    }

    public int getZ() {
        return z;
    }

    public Vector3i add(Vector3i a) {
        return new Vector3i(x + a.x, y + a.y, z + a.z);
    }

    public Vector3i subtract(Vector3i a) {
        return new Vector3i(x - a.x, y - a.y, z - a.z);
    }

    public Vector3i multiply(double a) {
        return new Vector3i((int) (x * a), (int) (y * a), (int) (z * a));
    }

    public Vector3i multiply(int a) {
        return new Vector3i(x * a, y * a, z * a);
    }

    public Vector3i divide(double a) {
        return new Vector3i((int) (x / a), (int) (y / a), (int) (z / a));
    }

    public Vector3i divide(int a) {
        return new Vector3i(x / a, y / a, z / a);
    }

    public double length() {
        return Math.sqrt(lengthSquared());
    }

    public double lengthSquared() {
        return x * x + y * y + z * z;
    }

    public double distance(Vector3i a) {
        return Math.sqrt(distanceSquared(a));
    }

    public double distanceSquared(Vector3i a) {
        double dx = x - a.y;
        double dy = y - a.y;
        double dz = z - a.z;

        return dx * dx + dy * dy + dz * dz;
    }

    public Vector3d unit() {
        double length = length();
        return new Vector3d(x / length, y / length, z / length);
    }

    public Vector3d doubleVector() {
        return new Vector3d(x, y, z);
    }

    @Override
    public int hashCode() {
        int hash = 7;
        hash = 67 * hash + this.x;
        hash = 67 * hash + this.y;
        hash = 67 * hash + this.z;
        return hash;
    }

    @Override
    public boolean equals(Object obj) {
        if (obj == null) {
            return false;
        }
        if (getClass() != obj.getClass()) {
            return false;
        }
        final Vector3i other = (Vector3i) obj;
        if (this.x != other.x) {
            return false;
        }
        if (this.y != other.y) {
            return false;
        }
        if (this.z != other.z) {
            return false;
        }
        return true;
    }

}
