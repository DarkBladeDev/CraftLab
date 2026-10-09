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
    private com.mcp.agent.props.PropManager propManager;
    private com.mcp.agent.pack.ResourcePackManager resourcePackManager;

    @Override
    public void onEnable() {
        saveDefaultConfig();

        getLogger().info("Starting Minecraft Content Platform Agent...");

        // 1. Storage
        this.itemStorage = new ItemStorage(getDataFolder(), getLogger());

        // 2. Adapter
        this.itemAdapter = new Paper121ItemAdapter();

        // 3. Resource Pack Manager & Listener
        this.resourcePackManager = new com.mcp.agent.pack.ResourcePackManager(getLogger());
        getServer().getPluginManager().registerEvents(new com.mcp.agent.pack.ResourcePackJoinListener(this.resourcePackManager), this);

        // 3b. Props Engine (Virtual Displays via PacketEvents)
        java.io.File propsDataDir = new java.io.File(getDataFolder(), "data");
        com.mcp.agent.props.PropStorage propStorage = new com.mcp.agent.props.PropStorage(propsDataDir, getLogger());
        this.propManager = new com.mcp.agent.props.PropManager(propStorage, this.itemStorage, getLogger());
        getServer().getPluginManager().registerEvents(new com.mcp.agent.props.PropPlaceBreakListener(this, this.propManager, this.itemStorage, this.itemAdapter, getLogger()), this);
        getServer().getPluginManager().registerEvents(new com.mcp.agent.props.PropInteractionListener(this, this.propManager, getLogger()), this);

        // 4. Oraxen Integration & WebSocket Client
        String gatewayUrl = getConfig().getString("gateway.url", "ws://127.0.0.1:8000/ws/agent");
        String targetId = getConfig().getString("gateway.targetId", "local-paper-server");
        String secret = getConfig().getString("gateway.secret", "dev-secret");
        int reconnectIntervalSeconds = getConfig().getInt("gateway.reconnectIntervalSeconds", 5);
        int heartbeatIntervalSeconds = getConfig().getInt("gateway.heartbeatIntervalSeconds", 15);

        java.io.File oraxenRoot = new java.io.File(getDataFolder().getParentFile(), "Oraxen");
        java.io.File oraxenItemsFolder = new java.io.File(oraxenRoot, "items");
        com.mcp.agent.adapters.oraxen.OraxenCatalogHook oraxenHook = new com.mcp.agent.adapters.oraxen.OraxenCatalogHook(getLogger());
        com.mcp.agent.adapters.oraxen.OraxenItemExporter oraxenExporter = new com.mcp.agent.adapters.oraxen.OraxenItemExporter(oraxenItemsFolder, getLogger());
        com.mcp.agent.adapters.oraxen.OraxenPackScanner oraxenPackScanner = new com.mcp.agent.adapters.oraxen.OraxenPackScanner(oraxenRoot, getLogger());

        this.wsClient = new AgentWebSocketClient(gatewayUrl, targetId, secret, reconnectIntervalSeconds, heartbeatIntervalSeconds,
                itemStorage, oraxenHook, oraxenExporter, this.resourcePackManager, oraxenPackScanner, this.propManager, getLogger());
        this.wsClient.start();

        // 5. Command
        McpCommand commandHandler = new McpCommand(this, itemStorage, itemAdapter, wsClient, this.resourcePackManager, this.propManager);
        PluginCommand cmd = getCommand("mcp");
        if (cmd != null) {
            cmd.setExecutor(commandHandler);
            cmd.setTabCompleter(commandHandler);
        }

        getLogger().info("MCP Agent enabled successfully!");
    }

    public void reloadPlugin() {
        getLogger().info("Reloading MCP Agent configuration and resources...");
        reloadConfig();

        String gatewayUrl = getConfig().getString("gateway.url", "ws://127.0.0.1:8000/ws/agent");
        String targetId = getConfig().getString("gateway.targetId", "local-paper-server");
        String secret = getConfig().getString("gateway.secret", "dev-secret");
        int reconnectIntervalSeconds = getConfig().getInt("gateway.reconnectIntervalSeconds", 5);
        int heartbeatIntervalSeconds = getConfig().getInt("gateway.heartbeatIntervalSeconds", 15);

        if (this.itemStorage != null) {
            this.itemStorage.loadAll();
        }

        if (this.propManager != null) {
            this.propManager.loadAll();
        }

        if (this.wsClient != null) {
            this.wsClient.updateConfiguration(gatewayUrl, targetId, secret, reconnectIntervalSeconds, heartbeatIntervalSeconds);
            this.wsClient.reconnect();
        }

        getLogger().info("MCP Agent configuration and resources reloaded successfully.");
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

    public com.mcp.agent.props.PropManager getPropManager() {
        return propManager;
    }

    public com.mcp.agent.pack.ResourcePackManager getResourcePackManager() {
        return resourcePackManager;
    }
}
