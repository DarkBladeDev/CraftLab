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

    @Test
    public void testResourcePackReadyIngestsGlyphsIntoStorage(@TempDir File tempDir) {
        Logger logger = Logger.getLogger("AgentTest");
        ItemStorage itemStorage = new ItemStorage(tempDir, logger);
        com.mcp.agent.storage.GlyphStorage glyphStorage = new com.mcp.agent.storage.GlyphStorage(tempDir, logger);

        AgentWebSocketClient client = new AgentWebSocketClient(
                "ws://127.0.0.1:8000/ws/agent",
                "test-server",
                "secret",
                5,
                15,
                itemStorage,
                null,
                null,
                null,
                null,
                null,
                glyphStorage,
                logger
        );

        String message = """
                {
                  "protocolVersion": "1.0",
                  "messageType": "event",
                  "messageId": "msg-1",
                  "targetId": "test-server",
                  "payload": {
                    "type": "resource_pack:ready",
                    "url": "http://127.0.0.1:8000/api/v1/packs/download/pack.zip",
                    "sha1": "0123456789abcdef0123456789abcdef01234567",
                    "required": true,
                    "prompt": "Download Pack",
                    "glyphs": [
                      {
                        "id": "badge_vip",
                        "namespace": "craftlab",
                        "hex": "E001",
                        "character": "\\uE001",
                        "placeholder": "%craftlab_glyph_badge_vip%"
                      },
                      {
                        "id": "crown",
                        "namespace": "ranks",
                        "hex": "E002",
                        "character": "\\uE002",
                        "placeholder": "%craftlab_glyph_ranks:crown%"
                      }
                    ]
                  }
                }
                """;

        client.handleIncomingMessage(message);

        assertNotNull(glyphStorage.getGlyph("badge_vip"));
        assertEquals("\uE001", com.mcp.agent.storage.GlyphStorage.extractCharacter(glyphStorage.getGlyph("badge_vip")));
        assertNotNull(glyphStorage.getGlyph("ranks:crown"));
        assertEquals("\uE002", com.mcp.agent.storage.GlyphStorage.extractCharacter(glyphStorage.getGlyph("ranks:crown")));
    }

    @Test
    public void testHandshakeAcceptedResponseIngestsGlyphs(@TempDir File tempDir) {
        Logger logger = Logger.getLogger("AgentTest");
        ItemStorage itemStorage = new ItemStorage(tempDir, logger);
        com.mcp.agent.storage.GlyphStorage glyphStorage = new com.mcp.agent.storage.GlyphStorage(tempDir, logger);

        AgentWebSocketClient client = new AgentWebSocketClient(
                "ws://127.0.0.1:8000/ws/agent",
                "test-server",
                "secret",
                5,
                15,
                itemStorage,
                null,
                null,
                null,
                null,
                null,
                glyphStorage,
                logger
        );

        String message = """
                {
                  "protocolVersion": "1.0",
                  "messageType": "response",
                  "messageId": "msg-accept-1",
                  "correlationId": "msg-hello-1",
                  "targetId": "test-server",
                  "payload": {
                    "status": "accepted",
                    "sessionId": "sess-test-server",
                    "negotiatedProtocol": "1.0",
                    "glyphs": [
                      {
                        "id": "coin",
                        "namespace": "craftlab",
                        "hex": "E010"
                      }
                    ]
                  }
                }
                """;

        client.handleIncomingMessage(message);

        assertNotNull(glyphStorage.getGlyph("coin"));
        assertEquals("\uE010", com.mcp.agent.storage.GlyphStorage.extractCharacter(glyphStorage.getGlyph("coin")));
    }

    @Test
    public void testHelloPayloadReportsPlaceholderApiWhenEnabled(@TempDir File tempDir) {
        Logger logger = Logger.getLogger("AgentTest");
        ItemStorage itemStorage = new ItemStorage(tempDir, logger);

        AgentWebSocketClient client = new AgentWebSocketClient(
                "ws://127.0.0.1:8000/ws/agent",
                "test-server",
                "secret",
                itemStorage,
                logger
        ) {
            @Override
            protected boolean isPlaceholderApiEnabled() {
                return true;
            }

            @Override
            protected String getPlaceholderApiVersion() {
                return "2.11.6";
            }
        };

        com.google.gson.JsonObject payload = client.buildHelloPayload();
        assertTrue(payload.has("detectedPlugins"));
        com.google.gson.JsonArray detected = payload.getAsJsonArray("detectedPlugins");
        assertEquals(1, detected.size());
        com.google.gson.JsonObject papi = detected.get(0).getAsJsonObject();
        assertEquals("PlaceholderAPI", papi.get("name").getAsString());
        assertEquals("2.11.6", papi.get("version").getAsString());
        assertTrue(papi.get("enabled").getAsBoolean());
    }
}
