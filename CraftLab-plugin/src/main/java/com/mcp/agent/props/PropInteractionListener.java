package com.mcp.agent.props;

import com.github.retrooper.packetevents.PacketEvents;
import com.github.retrooper.packetevents.protocol.entity.data.EntityData;
import com.github.retrooper.packetevents.protocol.entity.data.EntityDataTypes;
import com.github.retrooper.packetevents.protocol.entity.pose.EntityPose;
import com.github.retrooper.packetevents.wrapper.play.server.WrapperPlayServerEntityMetadata;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.entity.ArmorStand;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
import org.bukkit.util.Vector;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.Action;
import org.bukkit.event.entity.EntityDismountEvent;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerMoveEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.EquipmentSlot;
import org.bukkit.plugin.Plugin;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Logger;

public class PropInteractionListener implements Listener {
    private final Plugin plugin;
    private final PropManager propManager;
    private final Logger logger;
    private final Map<UUID, ArmorStand> activeSeats = new ConcurrentHashMap<>();
    private final Set<UUID> layingPlayers = ConcurrentHashMap.newKeySet();
    private final Map<UUID, Long> propInteractionCooldowns = new ConcurrentHashMap<>();

    public PropInteractionListener(Plugin plugin, PropManager propManager, Logger logger) {
        this.plugin = plugin;
        this.propManager = propManager;
        this.logger = logger;
    }

    @EventHandler(priority = EventPriority.NORMAL, ignoreCancelled = true)
    public void onPlayerInteractSeat(PlayerInteractEvent event) {
        if (event.getAction() != Action.RIGHT_CLICK_BLOCK) return;
        if (event.getHand() != EquipmentSlot.HAND) return;

        Block clicked = event.getClickedBlock();
        if (clicked == null || (clicked.getType() != Material.BARRIER && clicked.getType() != Material.STRUCTURE_VOID)) return;

        Player player = event.getPlayer();
        if (player.isSneaking()) return;
        if (player.isInsideVehicle()) return;

        String worldName = clicked.getWorld().getName();
        PropInstance instance = propManager.getInstanceAt(worldName, clicked.getX(), clicked.getY(), clicked.getZ());
        if (instance == null) return;

        PropDefinition def = propManager.getDefinition(instance.getPropId());
        if (def == null) return;

        if (def.getStates() != null && !def.getStates().isEmpty()) {
            long now = System.currentTimeMillis();
            Long lastInteraction = propInteractionCooldowns.get(instance.getInstanceId());
            if (lastInteraction != null && (now - lastInteraction) < 250) {
                event.setCancelled(true);
                return;
            }
            propInteractionCooldowns.put(instance.getInstanceId(), now);
            event.setCancelled(true);

            String currentStateKey = instance.getCurrentState();
            if (currentStateKey == null || currentStateKey.isEmpty()) {
                currentStateKey = def.getDefaultState();
            }
            PropDefinition.PropState currentStateObj = def.getState(currentStateKey);

            String nextStateKey = null;
            if (currentStateObj != null && currentStateObj.getNextState() != null && !currentStateObj.getNextState().trim().isEmpty()) {
                nextStateKey = currentStateObj.getNextState().trim();
            } else {
                List<String> keys = new ArrayList<>(def.getStates().keySet());
                if (!keys.isEmpty()) {
                    int idx = keys.indexOf(currentStateKey);
                    if (idx >= 0) {
                        nextStateKey = keys.get((idx + 1) % keys.size());
                    } else {
                        nextStateKey = keys.get(0);
                    }
                }
            }

            if (nextStateKey == null) {
                nextStateKey = def.getDefaultState();
            }

            // 1. Update in-memory state
            instance.setCurrentState(nextStateKey);

            // 2. Persist state asynchronously in SQLite
            final String stateToPersist = nextStateKey;
            try {
                org.bukkit.Bukkit.getScheduler().runTaskAsynchronously(plugin, () -> {
                    try {
                        propManager.getStorage().updateInstanceState(instance.getInstanceId(), stateToPersist);
                    } catch (Throwable t) {
                        logger.fine("Failed to update instance state in storage: " + t.getMessage());
                    }
                });
            } catch (Throwable t) {
                propManager.getStorage().updateInstanceState(instance.getInstanceId(), stateToPersist);
            }

            // 3. Broadcast visual model update
            propManager.broadcastStateUpdate(instance);

            // 4. Update dynamic lighting
            propManager.applyPropLighting(instance);

            // 5. Dynamic hitbox update with safe velocity ejection
            PropDefinition.PropState nextStateObj = def.getState(nextStateKey);
            handleDynamicHitboxTransition(instance, def, currentStateObj, nextStateObj);

            // 6. Play configured sound
            Location soundLoc = clicked.getLocation().add(0.5, 0.5, 0.5);
            playStateSound(soundLoc, nextStateObj);

            logger.info("Prop " + instance.getPropId() + " (" + instance.getInstanceId() + ") transitioned from '"
                    + currentStateKey + "' to '" + nextStateKey + "' by player " + player.getName());
            return;
        }

        String interType = def.getInteractionType();
        boolean isSeat = "seat".equalsIgnoreCase(interType);
        boolean isLay = "lay".equalsIgnoreCase(interType);
        if (!isSeat && !isLay) return;

        event.setCancelled(true);

        // Spawn temporary invisible seat entity centered above the clicked block
        float seatYOffset = def.getSeatHeight() > 0.0f ? def.getSeatHeight() : 0.5f;
        Location seatLoc = new Location(
                clicked.getWorld(),
                clicked.getX() + 0.5,
                clicked.getY() + seatYOffset,
                clicked.getZ() + 0.5,
                instance.getYaw(),
                0.0f
        );

        ArmorStand seat = clicked.getWorld().spawn(seatLoc, ArmorStand.class, as -> {
            as.setVisible(false);
            as.setMarker(true);
            as.setGravity(false);
            as.setInvulnerable(true);
            as.setPersistent(false);
            as.setSmall(true);
        });

        seat.addPassenger(player);
        activeSeats.put(player.getUniqueId(), seat);

        if (isLay) {
            layingPlayers.add(player.getUniqueId());
            sendPlayerPose(player, EntityPose.SLEEPING);
            org.bukkit.Bukkit.getScheduler().runTaskLater(plugin, () -> {
                if (layingPlayers.contains(player.getUniqueId())) {
                    sendPlayerPose(player, EntityPose.SLEEPING);
                }
            }, 1L);
        }

        clicked.getWorld().playSound(seatLoc, Sound.BLOCK_WOOD_STEP, 0.8f, 1.2f);
        logger.info("Player " + player.getName() + " interacted (" + interType + ") with prop " + instance.getPropId());
    }

    @EventHandler(priority = EventPriority.MONITOR)
    public void onPlayerDismount(EntityDismountEvent event) {
        Entity passenger = event.getEntity();
        if (!(passenger instanceof Player player)) return;

        ArmorStand seat = activeSeats.remove(player.getUniqueId());
        if (seat != null) {
            seat.remove();
            if (layingPlayers.remove(player.getUniqueId())) {
                sendPlayerPose(player, EntityPose.STANDING);
            }
            // Teleport slightly up/forward to avoid clipping
            Location loc = player.getLocation().add(0, 0.35, 0);
            player.teleport(loc);
            player.playSound(loc, Sound.BLOCK_WOOD_STEP, 0.8f, 0.9f);
        }
    }

    private void sendPlayerPose(Player player, EntityPose pose) {
        try {
            List<EntityData<?>> metadata = new ArrayList<>();
            // Index 6 in Minecraft 1.20+ is Entity Pose
            metadata.add(new EntityData<>(6, EntityDataTypes.ENTITY_POSE, pose));
            WrapperPlayServerEntityMetadata packet = new WrapperPlayServerEntityMetadata(player.getEntityId(), metadata);
            PacketEvents.getAPI().getPlayerManager().sendPacket(player, packet);
            for (Player viewer : player.getWorld().getPlayers()) {
                if (viewer.equals(player)) continue;
                if (viewer.getLocation().distanceSquared(player.getLocation()) <= (PropManager.TRACKING_RANGE * PropManager.TRACKING_RANGE)) {
                    PacketEvents.getAPI().getPlayerManager().sendPacket(viewer, packet);
                }
            }
        } catch (Throwable t) {
            logger.fine("Failed to send player pose packet: " + t.getMessage());
        }
    }

    @EventHandler(priority = EventPriority.MONITOR, ignoreCancelled = true)
    public void onPlayerMove(PlayerMoveEvent event) {
        Location from = event.getFrom();
        Location to = event.getTo();
        if (to == null) return;

        if (from.getBlockX() != to.getBlockX() || from.getBlockZ() != to.getBlockZ() || from.getBlockY() != to.getBlockY()) {
            propManager.updatePlayerView(event.getPlayer());
        }
    }

    @EventHandler(priority = EventPriority.MONITOR)
    public void onPlayerJoin(PlayerJoinEvent event) {
        // Delay slightly for client to complete chunk loading handshake
        org.bukkit.Bukkit.getScheduler().runTaskLater(plugin, () -> {
            if (event.getPlayer().isOnline()) {
                propManager.updatePlayerView(event.getPlayer());
            }
        }, 10L);
    }

    @EventHandler(priority = EventPriority.MONITOR)
    public void onPlayerQuit(PlayerQuitEvent event) {
        Player player = event.getPlayer();
        ArmorStand seat = activeSeats.remove(player.getUniqueId());
        if (seat != null) {
            seat.remove();
        }
        if (layingPlayers.remove(player.getUniqueId())) {
            sendPlayerPose(player, EntityPose.STANDING);
        }
        propManager.onPlayerQuit(player);
    }

    public boolean isCooldownActive(UUID instanceId) {
        Long last = propInteractionCooldowns.get(instanceId);
        return last != null && (System.currentTimeMillis() - last) < 250;
    }

    public Map<UUID, Long> getPropInteractionCooldowns() {
        return Collections.unmodifiableMap(propInteractionCooldowns);
    }

    public void handleDynamicHitboxTransition(PropInstance instance, PropDefinition def,
                                              PropDefinition.PropState oldState, PropDefinition.PropState newState) {
        String oldHitbox = (oldState != null && oldState.getHitboxType() != null)
                ? oldState.getHitboxType()
                : def.getHitboxType();
        String newHitbox = (newState != null && newState.getHitboxType() != null)
                ? newState.getHitboxType()
                : def.getHitboxType();

        if (oldHitbox == null) oldHitbox = "solid";
        if (newHitbox == null) newHitbox = "solid";

        if (oldHitbox.equalsIgnoreCase(newHitbox)) {
            return;
        }

        try {
            org.bukkit.World world = org.bukkit.Bukkit.getWorld(instance.getWorld());
            if (world == null) return;

            List<int[]> occupiedBlocks = propManager.getOccupiedBlocks(instance);

            if ("passable".equalsIgnoreCase(newHitbox)) {
                // Changing from solid to passable: replace BARRIER with STRUCTURE_VOID
                for (int[] coords : occupiedBlocks) {
                    Block b = world.getBlockAt(coords[0], coords[1], coords[2]);
                    if (b.getType() == Material.BARRIER) {
                        b.setType(Material.STRUCTURE_VOID);
                    }
                }
            } else {
                // Changing from passable to solid: safe eviction of any player inside bounding box
                Location propCenter = new Location(world, instance.getX() + 0.5, instance.getY() + 0.5, instance.getZ() + 0.5);

                for (Player p : world.getPlayers()) {
                    Location pLoc = p.getLocation();
                    for (int[] coords : occupiedBlocks) {
                        double minX = coords[0] - 0.3;
                        double maxX = coords[0] + 1.3;
                        double minY = coords[1] - 0.5;
                        double maxY = coords[1] + 1.8;
                        double minZ = coords[2] - 0.3;
                        double maxZ = coords[2] + 1.3;

                        if (pLoc.getX() >= minX && pLoc.getX() <= maxX &&
                            pLoc.getY() >= minY && pLoc.getY() <= maxY &&
                            pLoc.getZ() >= minZ && pLoc.getZ() <= maxZ) {

                            Vector push = pLoc.toVector().subtract(propCenter.toVector());
                            push.setY(0.0);
                            if (push.lengthSquared() < 0.0001) {
                                push = new Vector(0.0, 0.0, 1.0);
                            }
                            push.normalize().multiply(0.4).setY(0.15);
                            p.setVelocity(push);
                            break;
                        }
                    }
                }

                // Set collision blocks to BARRIER
                for (int[] coords : occupiedBlocks) {
                    Block b = world.getBlockAt(coords[0], coords[1], coords[2]);
                    if (b.getType() == Material.STRUCTURE_VOID || b.getType() == Material.AIR) {
                        b.setType(Material.BARRIER);
                    }
                }
            }
        } catch (Throwable t) {
            logger.fine("Failed to handle hitbox transition: " + t.getMessage());
        }
    }

    public void playStateSound(Location loc, PropDefinition.PropState state) {
        if (state == null || state.getSound() == null) return;
        PropDefinition.PropStateSound soundDef = state.getSound();
        String key = soundDef.getKey();
        if (key == null || key.trim().isEmpty()) return;

        float volume = soundDef.getVolume() > 0 ? soundDef.getVolume() : 1.0f;
        float pitch = soundDef.getPitch() > 0 ? soundDef.getPitch() : 1.0f;

        try {
            org.bukkit.World world = loc.getWorld();
            if (world == null) return;

            try {
                Sound bukkitSound = Sound.valueOf(key.toUpperCase().replace('.', '_'));
                world.playSound(loc, bukkitSound, volume, pitch);
            } catch (IllegalArgumentException e) {
                world.playSound(loc, key.toLowerCase(), volume, pitch);
            }
        } catch (Throwable t) {
            logger.fine("Failed to play prop sound: " + t.getMessage());
        }
    }
}
