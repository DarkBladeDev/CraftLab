package com.mcp.agent.props;

import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.Sound;
import org.bukkit.block.Block;
import org.bukkit.entity.ArmorStand;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
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

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Logger;

public class PropInteractionListener implements Listener {
    private final Plugin plugin;
    private final PropManager propManager;
    private final Logger logger;
    private final Map<UUID, ArmorStand> activeSeats = new ConcurrentHashMap<>();

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
        if (clicked == null || clicked.getType() != Material.BARRIER) return;

        Player player = event.getPlayer();
        if (player.isSneaking()) return;
        if (player.isInsideVehicle()) return;

        String worldName = clicked.getWorld().getName();
        PropInstance instance = propManager.getInstanceAt(worldName, clicked.getX(), clicked.getY(), clicked.getZ());
        if (instance == null) return;

        PropDefinition def = propManager.getDefinition(instance.getPropId());
        if (def == null || !"seat".equalsIgnoreCase(def.getInteractionType())) return;

        event.setCancelled(true);

        // Spawn temporary invisible seat entity
        float seatYOffset = def.getSeatHeight() - 0.2f;
        Location seatLoc = new Location(
                clicked.getWorld(),
                instance.getX() + 0.5,
                instance.getY() + seatYOffset,
                instance.getZ() + 0.5,
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

        clicked.getWorld().playSound(seatLoc, Sound.BLOCK_WOOD_STEP, 0.8f, 1.2f);
        logger.info("Player " + player.getName() + " sat on prop " + instance.getPropId());
    }

    @EventHandler(priority = EventPriority.MONITOR)
    public void onPlayerDismount(EntityDismountEvent event) {
        Entity passenger = event.getEntity();
        if (!(passenger instanceof Player player)) return;

        ArmorStand seat = activeSeats.remove(player.getUniqueId());
        if (seat != null) {
            seat.remove();
            // Teleport slightly up/forward to avoid clipping
            Location loc = player.getLocation().add(0, 0.35, 0);
            player.teleport(loc);
            player.playSound(loc, Sound.BLOCK_WOOD_STEP, 0.8f, 0.9f);
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
        propManager.onPlayerQuit(player);
    }
}
