package com.mcp.agent.net;

import com.mcp.agent.storage.ItemStorage;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.File;
import java.net.URI;
import java.util.logging.Logger;

import static org.junit.jupiter.api.Assertions.*;

public class AgentWebSocketClientTest {

    @Test
    public void testInitialConfigurationAndGetters(@TempDir File tempDir) {
        Logger logger = Logger.getLogger("AgentTest");
        ItemStorage storage = new ItemStorage(tempDir, logger);

        AgentWebSocketClient client = new AgentWebSocketClient(
                "ws://127.0.0.1:8000/ws/agent",
                "test-server",
                "secret-key",
                10,
                30,
                storage,
                null,
                null,
                null,
                null,
                null,
                logger
        );

        assertEquals(URI.create("ws://127.0.0.1:8000/ws/agent"), client.getGatewayUri());
        assertEquals("test-server", client.getTargetId());
        assertEquals("secret-key", client.getSecret());
        assertEquals(10, client.getReconnectIntervalSeconds());
        assertEquals(30, client.getHeartbeatIntervalSeconds());
    }

    @Test
    public void testUpdateConfiguration(@TempDir File tempDir) {
        Logger logger = Logger.getLogger("AgentTest");
        ItemStorage storage = new ItemStorage(tempDir, logger);

        AgentWebSocketClient client = new AgentWebSocketClient(
                "ws://127.0.0.1:8000/ws/agent",
                "initial-target",
                "initial-secret",
                storage,
                logger
        );

        assertEquals(5, client.getReconnectIntervalSeconds());
        assertEquals(15, client.getHeartbeatIntervalSeconds());

        client.updateConfiguration(
                "ws://192.168.1.50:9000/ws/agent",
                "prod-server",
                "new-prod-secret",
                8,
                20
        );

        assertEquals(URI.create("ws://192.168.1.50:9000/ws/agent"), client.getGatewayUri());
        assertEquals("prod-server", client.getTargetId());
        assertEquals("new-prod-secret", client.getSecret());
        assertEquals(8, client.getReconnectIntervalSeconds());
        assertEquals(20, client.getHeartbeatIntervalSeconds());
    }

    @Test
    public void testUpdateConfigurationWithInvalidUrlDoesNotCrash(@TempDir File tempDir) {
        Logger logger = Logger.getLogger("AgentTest");
        ItemStorage storage = new ItemStorage(tempDir, logger);

        AgentWebSocketClient client = new AgentWebSocketClient(
                "ws://127.0.0.1:8000/ws/agent",
                "target",
                "secret",
                storage,
                logger
        );

        URI originalUri = client.getGatewayUri();
        client.updateConfiguration(":::invalid-uri", "target", "secret", 5, 15);

        // Gateway URI remains original valid URI when invalid URL is supplied
        assertEquals(originalUri, client.getGatewayUri());
    }
}
