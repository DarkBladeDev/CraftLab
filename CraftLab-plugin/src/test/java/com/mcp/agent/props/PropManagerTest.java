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

    @Test
    public void testMetadataIndicesForMinecraft121() {
        // Ensure entity metadata indices align with Minecraft 1.20.5+ / 1.21.x ItemDisplay entity protocol specifications
        assertEquals(11, PropManager.METADATA_INDEX_TRANSLATION, "Translation must be index 11");
        assertEquals(12, PropManager.METADATA_INDEX_SCALE, "Scale must be index 12");
        assertEquals(13, PropManager.METADATA_INDEX_ROTATION_LEFT, "Rotation Left must be index 13");
        assertEquals(23, PropManager.METADATA_INDEX_ITEM_STACK, "Item display stack must be index 23");
        assertEquals(24, PropManager.METADATA_INDEX_ITEM_DISPLAY_CONTEXT, "Item display context must be index 24");
    }

    @Test
    public void testCardinalOffsetRotation() {
        // 1x1 Single Block: [0, 0, 0] remains [0, 0, 0] across all yaws
        for (float yaw : new float[]{0.0f, 90.0f, 180.0f, 270.0f}) {
            assertArrayEquals(new int[]{0, 0, 0}, PropManager.rotateOffset(0, 0, 0, yaw));
        }

        // 1x2 High (Pillar): [0, 1, 0] Y axis remains unchanged across all yaws
        for (float yaw : new float[]{0.0f, 90.0f, 180.0f, 270.0f}) {
            assertArrayEquals(new int[]{0, 1, 0}, PropManager.rotateOffset(0, 1, 0, yaw));
        }

        // 2x1 Long (Bench/Bed): [1, 0, 0]
        assertArrayEquals(new int[]{1, 0, 0}, PropManager.rotateOffset(1, 0, 0, 0.0f), "South: (dx, dy, dz)");
        assertArrayEquals(new int[]{0, 0, -1}, PropManager.rotateOffset(1, 0, 0, 90.0f), "West: (dz, dy, -dx)");
        assertArrayEquals(new int[]{-1, 0, 0}, PropManager.rotateOffset(1, 0, 0, 180.0f), "North: (-dx, dy, -dz)");
        assertArrayEquals(new int[]{0, 0, 1}, PropManager.rotateOffset(1, 0, 0, 270.0f), "East: (-dz, dy, dx)");

        // 2x2 Platform: [1, 0, 1]
        assertArrayEquals(new int[]{1, 0, 1}, PropManager.rotateOffset(1, 0, 1, 0.0f));
        assertArrayEquals(new int[]{1, 0, -1}, PropManager.rotateOffset(1, 0, 1, 90.0f));
        assertArrayEquals(new int[]{-1, 0, -1}, PropManager.rotateOffset(1, 0, 1, 180.0f));
        assertArrayEquals(new int[]{-1, 0, 1}, PropManager.rotateOffset(1, 0, 1, 270.0f));
    }

    @Test
    public void testMultiBlockRegistrationAndQuery(@TempDir File tempDir) {
        Logger logger = Logger.getLogger("PropManagerMultiBlockTest");
        PropStorage storage = new PropStorage(tempDir, logger);
        PropManager manager = new PropManager(storage, logger);

        // Define a 2x1 prop with offsets [0, 0, 0] and [1, 0, 0]
        PropDefinition bench = new PropDefinition("bench_2x1", "Oak Bench", "studio:item/bench");
        bench.setHitboxOffsets(java.util.Arrays.asList(new int[]{0, 0, 0}, new int[]{1, 0, 0}));
        manager.registerDefinition(bench);

        // Place prop facing West (yaw = 90 deg) at (100, 64, 200)
        // With 90 deg, [1, 0, 0] rotates to [0, 0, -1] -> (100, 64, 199)
        UUID benchId = UUID.randomUUID();
        PropInstance instance = new PropInstance(benchId, "bench_2x1", "world", 100, 64, 200, 90.0f, System.currentTimeMillis());
        manager.registerPlacedProp(instance);

        // Verify entity ID was assigned and is positive
        int entityId = manager.getEntityId(benchId);
        assertTrue(entityId > 0, "Entity ID should be assigned");

        // Verify anchor block occupancy and lookup
        assertTrue(manager.isBlockOccupied("world", 100, 64, 200));
        assertNotNull(manager.getInstanceAt("world", 100, 64, 200));
        assertEquals(benchId, manager.getInstanceAt("world", 100, 64, 200).getInstanceId());

        // Verify secondary rotated offset block (100, 64, 199) occupancy and lookup
        assertTrue(manager.isBlockOccupied("world", 100, 64, 199), "Secondary offset [0, 0, -1] must be marked occupied");
        assertNotNull(manager.getInstanceAt("world", 100, 64, 199), "Secondary offset must resolve parent instance");
        assertEquals(benchId, manager.getInstanceAt("world", 100, 64, 199).getInstanceId());

        // Verify occupied coordinates list
        List<int[]> occupied = manager.getOccupiedBlocks(instance);
        assertEquals(2, occupied.size());
        assertArrayEquals(new int[]{100, 64, 200}, occupied.get(0));
        assertArrayEquals(new int[]{100, 64, 199}, occupied.get(1));

        // Teardown: Remove placed prop
        manager.removePlacedProp(benchId);

        // Verify both blocks are de-registered
        assertFalse(manager.isBlockOccupied("world", 100, 64, 200));
        assertFalse(manager.isBlockOccupied("world", 100, 64, 199));
        assertNull(manager.getInstanceAt("world", 100, 64, 200));
        assertNull(manager.getInstanceAt("world", 100, 64, 199));
    }
}
