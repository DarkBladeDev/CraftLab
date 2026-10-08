package com.mcp.agent.props;

import java.util.UUID;

public class PropInstance {
    private final UUID instanceId;
    private final String propId;
    private final String world;
    private final int x;
    private final int y;
    private final int z;
    private final float yaw;
    private final long placedAt;

    public PropInstance(UUID instanceId, String propId, String world, int x, int y, int z, float yaw, long placedAt) {
        this.instanceId = instanceId;
        this.propId = propId;
        this.world = world;
        this.x = x;
        this.y = y;
        this.z = z;
        this.yaw = yaw;
        this.placedAt = placedAt;
    }

    public UUID getInstanceId() {
        return instanceId;
    }

    public String getPropId() {
        return propId;
    }

    public String getWorld() {
        return world;
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

    public float getYaw() {
        return yaw;
    }

    public long getPlacedAt() {
        return placedAt;
    }
}
