package com.mcp.agent.props;

import com.github.retrooper.packetevents.util.Quaternion4f;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.File;
import java.util.List;
import java.util.UUID;
import java.util.logging.Logger;

import static org.junit.jupiter.api.Assertions.*;

public class PropManagerTest {

    @Test
    public void testQuaternionCalculation() {
        // 0 deg (South)
        Quaternion4f q0 = PropManager.calculateRotationQuaternion(0.0f);
        assertEquals(0.0f, q0.getX(), 0.001f);
        assertEquals(0.0f, q0.getY(), 0.001f);
        assertEquals(0.0f, q0.getZ(), 0.001f);
        assertEquals(1.0f, q0.getW(), 0.001f);

        // 180 deg (North)
        Quaternion4f q180 = PropManager.calculateRotationQuaternion(180.0f);
        assertEquals(0.0f, q180.getX(), 0.001f);
        assertEquals(1.0f, q180.getY(), 0.001f);
        assertEquals(0.0f, q180.getZ(), 0.001f);
        assertEquals(0.0f, q180.getW(), 0.001f);

        // 90 deg (West)
        Quaternion4f q90 = PropManager.calculateRotationQuaternion(90.0f);
        assertEquals(0.0f, q90.getX(), 0.001f);
        assertEquals((float) Math.sin(Math.PI / 4.0), q90.getY(), 0.001f);
        assertEquals(0.0f, q90.getZ(), 0.001f);
        assertEquals((float) Math.cos(Math.PI / 4.0), q90.getW(), 0.001f);

        // 270 deg (East)
        Quaternion4f q270 = PropManager.calculateRotationQuaternion(270.0f);
        assertEquals(0.0f, q270.getX(), 0.001f);
        assertEquals((float) Math.sin(3.0 * Math.PI / 4.0), q270.getY(), 0.001f);
        assertEquals(0.0f, q270.getZ(), 0.001f);
        assertEquals((float) Math.cos(3.0 * Math.PI / 4.0), q270.getW(), 0.001f);
    }

    @Test
    public void testCardinalYawNormalization() {
        assertEquals(0.0f, PropManager.normalizeToCardinalYaw(10.0f));
        assertEquals(0.0f, PropManager.normalizeToCardinalYaw(350.0f));
        assertEquals(90.0f, PropManager.normalizeToCardinalYaw(85.0f));
        assertEquals(90.0f, PropManager.normalizeToCardinalYaw(110.0f));
        assertEquals(180.0f, PropManager.normalizeToCardinalYaw(170.0f));
        assertEquals(180.0f, PropManager.normalizeToCardinalYaw(190.0f));
        assertEquals(270.0f, PropManager.normalizeToCardinalYaw(260.0f));
        assertEquals(270.0f, PropManager.normalizeToCardinalYaw(280.0f));
    }

    @Test
    public void testSpatialChunkIndexAndQuery(@TempDir File tempDir) {
        Logger logger = Logger.getLogger("PropManagerTest");
        PropStorage storage = new PropStorage(tempDir, logger);
        PropManager manager = new PropManager(storage, logger);

        // Register definition
        PropDefinition def = new PropDefinition("oak_chair", "Oak Chair", "studio:furniture/oak_chair");
        manager.registerDefinition(def);
        assertNotNull(manager.getDefinition("oak_chair"));

        // Place prop at (100, 64, 200)
        UUID p1Id = UUID.randomUUID();
        PropInstance p1 = new PropInstance(p1Id, "oak_chair", "world", 100, 64, 200, 180.0f, System.currentTimeMillis());
        manager.registerPlacedProp(p1);

        // Place another prop at (105, 64, 205)
        UUID p2Id = UUID.randomUUID();
        PropInstance p2 = new PropInstance(p2Id, "oak_chair", "world", 105, 64, 205, 90.0f, System.currentTimeMillis());
        manager.registerPlacedProp(p2);

        // Place faraway prop at (500, 64, 500)
        UUID p3Id = UUID.randomUUID();
        PropInstance p3 = new PropInstance(p3Id, "oak_chair", "world", 500, 64, 500, 0.0f, System.currentTimeMillis());
        manager.registerPlacedProp(p3);

        // Query near (100, 200) within 32 blocks
        List<PropInstance> nearby = manager.getPropsNear("world", 100.0, 200.0, 32.0);
        assertEquals(2, nearby.size());
        assertTrue(nearby.stream().anyMatch(p -> p.getInstanceId().equals(p1Id)));
        assertTrue(nearby.stream().anyMatch(p -> p.getInstanceId().equals(p2Id)));
        assertFalse(nearby.stream().anyMatch(p -> p.getInstanceId().equals(p3Id)));

        // Remove p1
        manager.removePlacedProp(p1Id);
        List<PropInstance> afterRemove = manager.getPropsNear("world", 100.0, 200.0, 32.0);
        assertEquals(1, afterRemove.size());
        assertEquals(p2Id, afterRemove.get(0).getInstanceId());
    }
}
