package com.mcp.agent.commands;

import com.google.gson.JsonObject;
import com.mcp.agent.adapters.ItemAdapter;
import com.mcp.agent.net.AgentWebSocketClient;
import com.mcp.agent.storage.ItemStorage;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.Bukkit;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabCompleter;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

public class McpCommand implements CommandExecutor, TabCompleter {
    private final com.mcp.agent.core.McpAgentPlugin plugin;
    private final ItemStorage storage;
    private final ItemAdapter adapter;
    private final AgentWebSocketClient wsClient;
    private final com.mcp.agent.pack.ResourcePackManager packManager;
    private final com.mcp.agent.props.PropManager propManager;

    public McpCommand(ItemStorage storage, ItemAdapter adapter, AgentWebSocketClient wsClient) {
        this(null, storage, adapter, wsClient, null, null);
    }

    public McpCommand(ItemStorage storage, ItemAdapter adapter, AgentWebSocketClient wsClient, com.mcp.agent.pack.ResourcePackManager packManager) {
        this(null, storage, adapter, wsClient, packManager, null);
    }

    public McpCommand(ItemStorage storage, ItemAdapter adapter, AgentWebSocketClient wsClient, com.mcp.agent.pack.ResourcePackManager packManager, com.mcp.agent.props.PropManager propManager) {
        this(null, storage, adapter, wsClient, packManager, propManager);
    }

    public McpCommand(com.mcp.agent.core.McpAgentPlugin plugin, ItemStorage storage, ItemAdapter adapter, AgentWebSocketClient wsClient, com.mcp.agent.pack.ResourcePackManager packManager, com.mcp.agent.props.PropManager propManager) {
        this.plugin = plugin;
        this.storage = storage;
        this.adapter = adapter;
        this.wsClient = wsClient;
        this.packManager = packManager;
        this.propManager = propManager;
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (args.length == 0) {
            sender.sendMessage(Component.text("Usage: /mcp [give|status|reload|reloadpack]", NamedTextColor.YELLOW));
            return true;
        }

        String sub = args[0].toLowerCase();

        if ("status".equals(sub)) {
            AgentWebSocketClient activeWs = plugin != null ? plugin.getWsClient() : wsClient;
            boolean connected = activeWs != null && activeWs.isConnected();
            NamedTextColor statusColor = connected ? NamedTextColor.GREEN : NamedTextColor.RED;
            sender.sendMessage(Component.text("--- MCP Agent Status ---", NamedTextColor.GOLD));
            sender.sendMessage(Component.text("Gateway: ", NamedTextColor.GRAY)
                    .append(Component.text(connected ? "Connected" : "Disconnected", statusColor)));
            if (activeWs != null) {
                sender.sendMessage(Component.text("Target ID: ", NamedTextColor.GRAY)
                        .append(Component.text(activeWs.getTargetId(), NamedTextColor.YELLOW)));
                sender.sendMessage(Component.text("Gateway URL: ", NamedTextColor.GRAY)
                        .append(Component.text(activeWs.getGatewayUri().toString(), NamedTextColor.AQUA)));
            }
            ItemStorage activeStorage = (plugin != null && plugin.getItemStorage() != null) ? plugin.getItemStorage() : storage;
            com.mcp.agent.props.PropManager activeProps = (plugin != null && plugin.getPropManager() != null) ? plugin.getPropManager() : propManager;
            int itemsCount = activeStorage != null ? activeStorage.getAllItems().size() : 0;
            sender.sendMessage(Component.text("Registered Items: ", NamedTextColor.GRAY)
                    .append(Component.text(itemsCount, NamedTextColor.AQUA)));
            if (activeProps != null) {
                sender.sendMessage(Component.text("Registered Blocks/Props: ", NamedTextColor.GRAY)
                        .append(Component.text(activeProps.getDefinitions().size(), NamedTextColor.LIGHT_PURPLE)));
            }
            return true;
        }

        if ("reload".equals(sub)) {
            if (plugin != null) {
                plugin.reloadPlugin();
            } else {
                if (storage != null) {
                    storage.loadAll();
                }
                if (propManager != null) {
                    propManager.loadAll();
                }
                if (wsClient != null) {
                    wsClient.reconnect();
                }
            }
            ItemStorage activeStorage = (plugin != null && plugin.getItemStorage() != null) ? plugin.getItemStorage() : storage;
            com.mcp.agent.props.PropManager activeProps = (plugin != null && plugin.getPropManager() != null) ? plugin.getPropManager() : propManager;
            int itemsCount = activeStorage != null ? activeStorage.getAllItems().size() : 0;
            int propsCount = activeProps != null ? activeProps.getDefinitions().size() : 0;
            sender.sendMessage(Component.text("[MCP] Configuration and local storage reloaded. " + itemsCount + " items, " + propsCount + " blocks/props active.", NamedTextColor.GREEN));
            return true;
        }

        if ("give".equals(sub)) {
            Player targetPlayer;
            String itemId;

            if (args.length >= 3) {
                targetPlayer = Bukkit.getPlayerExact(args[1]);
                if (targetPlayer == null) {
                    sender.sendMessage(Component.text("Player '" + args[1] + "' is not online.", NamedTextColor.RED));
                    return true;
                }
                itemId = args[2];
            } else if (args.length == 2 && sender instanceof Player player) {
                targetPlayer = player;
                itemId = args[1];
            } else {
                sender.sendMessage(Component.text("Usage: /mcp give <player> <item_or_prop_id> (or /mcp give <id> for self)", NamedTextColor.RED));
                return true;
            }

            JsonObject itemJson = storage.getItem(itemId);
            if (itemJson != null) {
                ItemStack stack = adapter.compile(itemJson);
                targetPlayer.getInventory().addItem(stack);
                sender.sendMessage(Component.text("[MCP] Gave 1x '" + itemId + "' to " + targetPlayer.getName() + ".", NamedTextColor.GREEN));
                return true;
            }

            if (propManager != null) {
                com.mcp.agent.props.PropDefinition propDef = propManager.getDefinition(itemId);
                if (propDef != null) {
                    ItemStack stack = com.mcp.agent.props.PropPlaceBreakListener.createPropItemStack(propDef, itemId, storage, adapter);
                    targetPlayer.getInventory().addItem(stack);
                    sender.sendMessage(Component.text("[MCP] Gave 1x prop/block '" + itemId + "' to " + targetPlayer.getName() + ".", NamedTextColor.GREEN));
                    return true;
                }
            }

            sender.sendMessage(Component.text("Resource '" + itemId + "' not found in MCP registry.", NamedTextColor.RED));
            return true;
        }

        if ("reloadpack".equals(sub)) {
            if (packManager == null || !packManager.hasActivePack()) {
                sender.sendMessage(Component.text("[MCP] No active resource pack is currently configured.", NamedTextColor.RED));
                return true;
            }

            if (args.length >= 2 && "all".equalsIgnoreCase(args[1])) {
                if (!sender.hasPermission("mcp.admin.reloadpack") && !sender.isOp()) {
                    sender.sendMessage(Component.text("You do not have permission to prompt all players.", NamedTextColor.RED));
                    return true;
                }
                int count = packManager.promptAllOnlinePlayers();
                sender.sendMessage(Component.text("[MCP] Re-prompted resource pack to " + count + " player(s).", NamedTextColor.GREEN));
                return true;
            }

            if (sender instanceof Player player) {
                packManager.applyToPlayer(player);
                sender.sendMessage(Component.text("[MCP] Re-applying resource pack...", NamedTextColor.GREEN));
            } else {
                sender.sendMessage(Component.text("Console can only use: /mcp reloadpack all", NamedTextColor.YELLOW));
            }
            return true;
        }

        sender.sendMessage(Component.text("Unknown subcommand. Use /mcp [give|status|reload|reloadpack]", NamedTextColor.RED));
        return true;
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String label, String[] args) {
        if (args.length == 1) {
            return Arrays.asList("give", "status", "reload", "reloadpack");
        }
        if (args.length == 2 && "reloadpack".equalsIgnoreCase(args[0])) {
            return Collections.singletonList("all");
        }
        if (args.length == 2 && "give".equalsIgnoreCase(args[0])) {
            List<String> list = new ArrayList<>();
            for (Player p : Bukkit.getOnlinePlayers()) {
                list.add(p.getName());
            }
            list.addAll(storage.getAllItems().keySet());
            if (propManager != null) {
                list.addAll(propManager.getDefinitions().keySet());
            }
            return list;
        }
        if (args.length == 3 && "give".equalsIgnoreCase(args[0])) {
            List<String> list = new ArrayList<>(storage.getAllItems().keySet());
            if (propManager != null) {
                list.addAll(propManager.getDefinitions().keySet());
            }
            return list;
        }
        return Collections.emptyList();
    }
}
