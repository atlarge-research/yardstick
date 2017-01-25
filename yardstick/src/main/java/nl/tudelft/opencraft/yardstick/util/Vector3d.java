package nl.tudelft.opencraft.yardstick.util;

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
        return new Vector3i((int) x, (int) y, (int) z);
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
        return "Vector3d{" +
                "x=" + x +
                ", y=" + y +
                ", z=" + z +
                '}';
    }

    @Override
    public boolean equals(Object obj) {
        if (obj == null) {
            return false;
        }
        if (getClass() != obj.getClass()) {
            return false;
        }
        final Vector3d other = (Vector3d) obj;
        if (Double.doubleToLongBits(this.x) != Double.doubleToLongBits(other.x)) {
            return false;
        }
        if (Double.doubleToLongBits(this.y) != Double.doubleToLongBits(other.y)) {
            return false;
        }
        if (Double.doubleToLongBits(this.z) != Double.doubleToLongBits(other.z)) {
            return false;
        }
        return true;
    }

}
