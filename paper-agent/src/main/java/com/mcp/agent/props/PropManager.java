package com.mcp.agent.props;

import com.github.retrooper.packetevents.PacketEvents;
import com.github.retrooper.packetevents.protocol.entity.data.EntityData;
import com.github.retrooper.packetevents.protocol.entity.data.EntityDataTypes;
import com.github.retrooper.packetevents.protocol.entity.type.EntityTypes;
import com.github.retrooper.packetevents.util.Quaternion4f;
import com.github.retrooper.packetevents.util.Vector3d;
import com.github.retrooper.packetevents.util.Vector3f;
import com.github.retrooper.packetevents.wrapper.play.server.WrapperPlayServerDestroyEntities;
import com.github.retrooper.packetevents.wrapper.play.server.WrapperPlayServerEntityMetadata;
import com.github.retrooper.packetevents.wrapper.play.server.WrapperPlayServerSpawnEntity;
import io.github.retrooper.packetevents.util.SpigotConversionUtil;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.logging.Logger;

public class PropManager {
    public static final double TRACKING_RANGE = 32.0;

    private final PropStorage storage;
    private final Logger logger;
    private final Map<String, PropDefinition> definitions = new ConcurrentHashMap<>();
    private final Map<UUID, PropInstance> instancesById = new ConcurrentHashMap<>();
    private final Map<String, Map<Long, List<PropInstance>>> chunkSpatialIndex = new ConcurrentHashMap<>();
    private final Map<UUID, Integer> instanceToEntityId = new ConcurrentHashMap<>();
    private final Map<UUID, Set<UUID>> playersViewingProps = new ConcurrentHashMap<>();
    private final AtomicInteger nextEntityId = new AtomicInteger(2_000_000);

    public PropManager(PropStorage storage, Logger logger) {
        this.storage = storage;
        this.logger = logger;
        loadAll();
    }

    public void loadAll() {
        definitions.clear();
        instancesById.clear();
        chunkSpatialIndex.clear();

        definitions.putAll(storage.getAllDefinitions());
        for (PropInstance instance : storage.getAllInstances()) {
            addInstanceToMemory(instance);
        }
        logger.info("Loaded " + definitions.size() + " prop definitions and " + instancesById.size() + " placed props.");
    }

    public void registerDefinition(PropDefinition def) {
        definitions.put(def.getId(), def);
        storage.saveDefinition(def);
    }

    public PropDefinition getDefinition(String id) {
        return definitions.get(id);
    }

    public Map<String, PropDefinition> getDefinitions() {
        return Collections.unmodifiableMap(definitions);
    }

    public synchronized void registerPlacedProp(PropInstance instance) {
        addInstanceToMemory(instance);
        storage.saveInstance(instance);
    }

    public synchronized void removePlacedProp(UUID instanceId) {
        PropInstance instance = instancesById.remove(instanceId);
        if (instance != null) {
            removeInstanceFromSpatialIndex(instance);
            storage.removeInstance(instanceId);
            instanceToEntityId.remove(instanceId);
        }
    }

    public PropInstance getInstance(UUID instanceId) {
        return instancesById.get(instanceId);
    }

    public PropInstance getInstanceAt(String world, int x, int y, int z) {
        return storage.getInstanceAt(world, x, y, z);
    }

    public List<PropInstance> getAllInstances() {
        return new ArrayList<>(instancesById.values());
    }

    private void addInstanceToMemory(PropInstance instance) {
        instancesById.put(instance.getInstanceId(), instance);
        instanceToEntityId.computeIfAbsent(instance.getInstanceId(), k -> nextEntityId.incrementAndGet());

        long chunkKey = getChunkKey(instance.getX() >> 4, instance.getZ() >> 4);
        chunkSpatialIndex
                .computeIfAbsent(instance.getWorld(), w -> new ConcurrentHashMap<>())
                .computeIfAbsent(chunkKey, c -> Collections.synchronizedList(new ArrayList<>()))
                .add(instance);
    }

    private void removeInstanceFromSpatialIndex(PropInstance instance) {
        long chunkKey = getChunkKey(instance.getX() >> 4, instance.getZ() >> 4);
        Map<Long, List<PropInstance>> worldChunks = chunkSpatialIndex.get(instance.getWorld());
        if (worldChunks != null) {
            List<PropInstance> list = worldChunks.get(chunkKey);
            if (list != null) {
                list.remove(instance);
            }
        }
    }

    public List<PropInstance> getPropsNear(String world, double x, double z, double maxDistance) {
        List<PropInstance> result = new ArrayList<>();
        int minChunkX = (int) Math.floor((x - maxDistance) / 16.0);
        int maxChunkX = (int) Math.floor((x + maxDistance) / 16.0);
        int minChunkZ = (int) Math.floor((z - maxDistance) / 16.0);
        int maxChunkZ = (int) Math.floor((z + maxDistance) / 16.0);

        Map<Long, List<PropInstance>> worldChunks = chunkSpatialIndex.get(world);
        if (worldChunks == null) return result;

        double maxDistSq = maxDistance * maxDistance;

        for (int cx = minChunkX; cx <= maxChunkX; cx++) {
            for (int cz = minChunkZ; cz <= maxChunkZ; cz++) {
                List<PropInstance> chunkProps = worldChunks.get(getChunkKey(cx, cz));
                if (chunkProps != null) {
                    synchronized (chunkProps) {
                        for (PropInstance p : chunkProps) {
                            double dx = (p.getX() + 0.5) - x;
                            double dz = (p.getZ() + 0.5) - z;
                            if ((dx * dx + dz * dz) <= maxDistSq) {
                                result.add(p);
                            }
                        }
                    }
                }
            }
        }
        return result;
    }

    public void updatePlayerView(Player player) {
        if (!player.isOnline()) return;

        Location loc = player.getLocation();
        String world = loc.getWorld().getName();
        double px = loc.getX();
        double pz = loc.getZ();

        List<PropInstance> nearby = getPropsNear(world, px, pz, TRACKING_RANGE);
        Set<UUID> nearbyIds = new HashSet<>();
        for (PropInstance p : nearby) {
            nearbyIds.add(p.getInstanceId());
        }

        Set<UUID> currentlyViewing = playersViewingProps.computeIfAbsent(player.getUniqueId(), k -> ConcurrentHashMap.newKeySet());

        // Spawn newly visible
        for (PropInstance prop : nearby) {
            if (!currentlyViewing.contains(prop.getInstanceId())) {
                spawnPropForPlayer(player, prop);
                currentlyViewing.add(prop.getInstanceId());
            }
        }

        // Destroy out-of-range
        Iterator<UUID> iter = currentlyViewing.iterator();
        while (iter.hasNext()) {
            UUID propId = iter.next();
            if (!nearbyIds.contains(propId)) {
                PropInstance instance = instancesById.get(propId);
                if (instance != null) {
                    destroyPropForPlayer(player, instance);
                } else {
                    int entityId = instanceToEntityId.getOrDefault(propId, -1);
                    if (entityId != -1) {
                        sendPacket(player, new WrapperPlayServerDestroyEntities(entityId));
                    }
                }
                iter.remove();
            }
        }
    }

    public void spawnPropForPlayer(Player player, PropInstance prop) {
        int entityId = instanceToEntityId.computeIfAbsent(prop.getInstanceId(), k -> nextEntityId.incrementAndGet());
        PropDefinition def = definitions.get(prop.getPropId());

        // 1. Spawn ITEM_DISPLAY entity at anchor coordinate centered
        double spawnX = prop.getX() + 0.5;
        double spawnY = prop.getY();
        double spawnZ = prop.getZ() + 0.5;

        WrapperPlayServerSpawnEntity spawnPacket = new WrapperPlayServerSpawnEntity(
                entityId,
                Optional.of(UUID.randomUUID()),
                EntityTypes.ITEM_DISPLAY,
                new Vector3d(spawnX, spawnY, spawnZ),
                prop.getYaw(),
                0.0f,
                0.0f,
                0,
                Optional.empty()
        );
        sendPacket(player, spawnPacket);

        // 2. Set Entity Metadata (Scale, Translation, Rotation quaternion, Item display)
        List<EntityData<?>> metadata = new ArrayList<>();

        // Scale
        float sx = 1.0f, sy = 1.0f, sz = 1.0f;
        if (def != null && def.getScale() != null && def.getScale().size() >= 3) {
            sx = def.getScale().get(0);
            sy = def.getScale().get(1);
            sz = def.getScale().get(2);
        }
        metadata.add(new EntityData<>(16, EntityDataTypes.VECTOR3F, new Vector3f(sx, sy, sz)));

        // Translation
        float tx = 0.0f, ty = 0.0f, tz = 0.0f;
        if (def != null && def.getTranslation() != null && def.getTranslation().size() >= 3) {
            tx = def.getTranslation().get(0);
            ty = def.getTranslation().get(1);
            tz = def.getTranslation().get(2);
        }
        metadata.add(new EntityData<>(15, EntityDataTypes.VECTOR3F, new Vector3f(tx, ty, tz)));

        // Rotation Quaternion
        Quaternion4f rotQuaternion = calculateRotationQuaternion(prop.getYaw());
        metadata.add(new EntityData<>(17, EntityDataTypes.QUATERNION, rotQuaternion));

        // Display Item
        ItemStack displayItem = createDisplayItemStack(def);
        if (displayItem != null) {
            com.github.retrooper.packetevents.protocol.item.ItemStack peItem =
                    SpigotConversionUtil.fromBukkitItemStack(displayItem);
            metadata.add(new EntityData<>(23, EntityDataTypes.ITEMSTACK, peItem));
        }

        WrapperPlayServerEntityMetadata metaPacket = new WrapperPlayServerEntityMetadata(entityId, metadata);
        sendPacket(player, metaPacket);
    }

    public void destroyPropForPlayer(Player player, PropInstance prop) {
        int entityId = instanceToEntityId.getOrDefault(prop.getInstanceId(), -1);
        if (entityId != -1) {
            WrapperPlayServerDestroyEntities destroyPacket = new WrapperPlayServerDestroyEntities(entityId);
            sendPacket(player, destroyPacket);
        }
    }

    public void broadcastSpawn(PropInstance instance) {
        for (Player player : org.bukkit.Bukkit.getOnlinePlayers()) {
            if (player.getWorld().getName().equals(instance.getWorld())) {
                double distSq = player.getLocation().distanceSquared(new Location(player.getWorld(), instance.getX() + 0.5, instance.getY(), instance.getZ() + 0.5));
                if (distSq <= (TRACKING_RANGE * TRACKING_RANGE)) {
                    spawnPropForPlayer(player, instance);
                    Set<UUID> viewing = playersViewingProps.computeIfAbsent(player.getUniqueId(), k -> ConcurrentHashMap.newKeySet());
                    viewing.add(instance.getInstanceId());
                }
            }
        }
    }

    public void broadcastDestroy(PropInstance instance) {
        int entityId = instanceToEntityId.getOrDefault(instance.getInstanceId(), -1);
        if (entityId == -1) return;

        WrapperPlayServerDestroyEntities destroyPacket = new WrapperPlayServerDestroyEntities(entityId);
        for (Player player : org.bukkit.Bukkit.getOnlinePlayers()) {
            Set<UUID> viewing = playersViewingProps.get(player.getUniqueId());
            if (viewing != null && viewing.remove(instance.getInstanceId())) {
                sendPacket(player, destroyPacket);
            }
        }
    }

    public void onPlayerQuit(Player player) {
        playersViewingProps.remove(player.getUniqueId());
    }

    private void sendPacket(Player player, com.github.retrooper.packetevents.wrapper.PacketWrapper<?> packet) {
        try {
            PacketEvents.getAPI().getPlayerManager().sendPacket(player, packet);
        } catch (Exception e) {
            // PacketEvents might not be active in mock unit test environments
            logger.fine("Failed to send packet to " + player.getName() + ": " + e.getMessage());
        }
    }

    private ItemStack createDisplayItemStack(PropDefinition def) {
        ItemStack item = new ItemStack(Material.PAPER);
        ItemMeta meta = item.getItemMeta();
        if (meta != null) {
            if (def != null && def.getDisplayName() != null) {
                meta.setDisplayName(def.getDisplayName());
            }
            if (def != null && def.getItemModel() != null) {
                try {
                    // Try to apply item_model component via Paper 1.21.2+ API if present
                    org.bukkit.NamespacedKey key = org.bukkit.NamespacedKey.fromString(def.getItemModel());
                    if (key != null) {
                        try {
                            java.lang.reflect.Method m = meta.getClass().getMethod("setItemModel", org.bukkit.NamespacedKey.class);
                            m.invoke(meta, key);
                        } catch (NoSuchMethodException ignored) {
                            // Fallback to custom model data hash if setItemModel is not present
                            meta.setCustomModelData(Math.abs(def.getItemModel().hashCode() % 1000000));
                        }
                    }
                } catch (Exception ignored) {
                }
            }
            item.setItemMeta(meta);
        }
        return item;
    }

    public static Quaternion4f calculateRotationQuaternion(float yaw) {
        float normalizedYaw = normalizeToCardinalYaw(yaw);
        double rad = Math.toRadians(normalizedYaw);
        float y = (float) Math.sin(rad / 2.0);
        float w = (float) Math.cos(rad / 2.0);
        return new Quaternion4f(0.0f, y, 0.0f, w);
    }

    public static float normalizeToCardinalYaw(float yaw) {
        float normalized = (yaw % 360.0f + 360.0f) % 360.0f;
        if (normalized >= 45.0f && normalized < 135.0f) {
            return 90.0f; // WEST
        } else if (normalized >= 135.0f && normalized < 225.0f) {
            return 180.0f; // NORTH
        } else if (normalized >= 225.0f && normalized < 315.0f) {
            return 270.0f; // EAST
        } else {
            return 0.0f; // SOUTH
        }
    }

    public static long getChunkKey(int chunkX, int chunkZ) {
        return (((long) chunkX) << 32) | (((long) chunkZ) & 0xFFFFFFFFL);
    }
}
