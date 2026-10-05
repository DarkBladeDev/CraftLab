package com.mcp.agent.core;

import com.mcp.agent.adapters.ItemAdapter;
import com.mcp.agent.adapters.Paper121ItemAdapter;
import com.mcp.agent.commands.McpCommand;
import com.mcp.agent.net.AgentWebSocketClient;
import com.mcp.agent.storage.ItemStorage;
import org.bukkit.command.PluginCommand;
import org.bukkit.plugin.java.JavaPlugin;

public class McpAgentPlugin extends JavaPlugin {
    private ItemStorage itemStorage;
    private ItemAdapter itemAdapter;
    private AgentWebSocketClient wsClient;

    @Override
    public void onEnable() {
        saveDefaultConfig();

        getLogger().info("Starting Minecraft Content Platform Agent...");

        // 1. Storage
        this.itemStorage = new ItemStorage(getDataFolder(), getLogger());

        // 2. Adapter
        this.itemAdapter = new Paper121ItemAdapter();

        // 3. Oraxen Integration & WebSocket Client
        String gatewayUrl = getConfig().getString("gateway.url", "ws://127.0.0.1:8000/ws/agent");
        String targetId = getConfig().getString("gateway.targetId", "local-paper-server");
        String secret = getConfig().getString("gateway.secret", "dev-secret");

        java.io.File oraxenFolder = new java.io.File(getDataFolder().getParentFile(), "Oraxen/items");
        com.mcp.agent.adapters.oraxen.OraxenCatalogHook oraxenHook = new com.mcp.agent.adapters.oraxen.OraxenCatalogHook(getLogger());
        com.mcp.agent.adapters.oraxen.OraxenItemExporter oraxenExporter = new com.mcp.agent.adapters.oraxen.OraxenItemExporter(oraxenFolder, getLogger());

        this.wsClient = new AgentWebSocketClient(gatewayUrl, targetId, secret, itemStorage, oraxenHook, oraxenExporter, getLogger());
        this.wsClient.start();

        // 4. Command
        McpCommand commandHandler = new McpCommand(itemStorage, itemAdapter, wsClient);
        PluginCommand cmd = getCommand("mcp");
        if (cmd != null) {
            cmd.setExecutor(commandHandler);
            cmd.setTabCompleter(commandHandler);
        }

        getLogger().info("MCP Agent enabled successfully!");
    }

    @Override
    public void onDisable() {
        getLogger().info("Disabling MCP Agent...");
        if (wsClient != null) {
            wsClient.stop();
        }
        getLogger().info("MCP Agent disabled.");
    }

    public ItemStorage getItemStorage() {
        return itemStorage;
    }

    public ItemAdapter getItemAdapter() {
        return itemAdapter;
    }

    public AgentWebSocketClient getWsClient() {
        return wsClient;
    }
}
