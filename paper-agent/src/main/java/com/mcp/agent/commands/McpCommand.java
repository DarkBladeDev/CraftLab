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
    private final ItemStorage storage;
    private final ItemAdapter adapter;
    private final AgentWebSocketClient wsClient;

    public McpCommand(ItemStorage storage, ItemAdapter adapter, AgentWebSocketClient wsClient) {
        this.storage = storage;
        this.adapter = adapter;
        this.wsClient = wsClient;
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (args.length == 0) {
            sender.sendMessage(Component.text("Usage: /mcp [give|status|reload]", NamedTextColor.YELLOW));
            return true;
        }

        String sub = args[0].toLowerCase();

        if ("status".equals(sub)) {
            boolean connected = wsClient != null && wsClient.isConnected();
            NamedTextColor statusColor = connected ? NamedTextColor.GREEN : NamedTextColor.RED;
            sender.sendMessage(Component.text("--- MCP Agent Status ---", NamedTextColor.GOLD));
            sender.sendMessage(Component.text("Gateway: ", NamedTextColor.GRAY)
                    .append(Component.text(connected ? "Connected" : "Disconnected", statusColor)));
            sender.sendMessage(Component.text("Registered Items: ", NamedTextColor.GRAY)
                    .append(Component.text(storage.getAllItems().size(), NamedTextColor.AQUA)));
            return true;
        }

        if ("reload".equals(sub)) {
            storage.loadAll();
            sender.sendMessage(Component.text("[MCP] Local storage reloaded. " + storage.getAllItems().size() + " items active.", NamedTextColor.GREEN));
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
                sender.sendMessage(Component.text("Usage: /mcp give <player> <item_id> (or /mcp give <item_id> for self)", NamedTextColor.RED));
                return true;
            }

            JsonObject itemJson = storage.getItem(itemId);
            if (itemJson == null) {
                sender.sendMessage(Component.text("Item '" + itemId + "' not found in MCP registry.", NamedTextColor.RED));
                return true;
            }

            ItemStack stack = adapter.compile(itemJson);
            targetPlayer.getInventory().addItem(stack);
            sender.sendMessage(Component.text("[MCP] Gave 1x '" + itemId + "' to " + targetPlayer.getName() + ".", NamedTextColor.GREEN));
            return true;
        }

        sender.sendMessage(Component.text("Unknown subcommand. Use /mcp [give|status|reload]", NamedTextColor.RED));
        return true;
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String label, String[] args) {
        if (args.length == 1) {
            return Arrays.asList("give", "status", "reload");
        }
        if (args.length == 2 && "give".equalsIgnoreCase(args[0])) {
            List<String> list = new ArrayList<>();
            for (Player p : Bukkit.getOnlinePlayers()) {
                list.add(p.getName());
            }
            list.addAll(storage.getAllItems().keySet());
            return list;
        }
        if (args.length == 3 && "give".equalsIgnoreCase(args[0])) {
            return new ArrayList<>(storage.getAllItems().keySet());
        }
        return Collections.emptyList();
    }
}
