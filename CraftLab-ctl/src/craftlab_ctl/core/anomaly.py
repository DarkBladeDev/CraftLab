import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from craftlab_security import SecurityAuditSink


class AnomalyAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    rule: str
    title: str
    description: str
    severity: str  # "critical", "high", "medium", "low"
    source_ip: Optional[str] = None
    target_actor: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SecurityPosture(BaseModel):
    threat_index: int  # 0 to 100
    classification: str  # "NORMAL", "ELEVATED", "HIGH", "CRITICAL", "LOCKDOWN"
    failed_auths_15m: int
    active_alerts_count: int
    quarantined_ips_count: int
    lockdown_enabled: bool = False
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SecurityAnomalyEvaluator:
    """
    Evaluates rolling sliding-window events from SecurityAuditSink to identify
    anomalous patterns, compute the system threat index, and produce actionable alerts.
    """

    def __init__(self, sink: Optional[SecurityAuditSink] = None, window_minutes: int = 15):
        self.sink = sink
        self.window_minutes = window_minutes
        self._dismissed_alert_ids: set = set()

    def dismiss_alert(self, alert_id: str) -> None:
        self._dismissed_alert_ids.add(alert_id)

    def clear_dismissed(self) -> None:
        self._dismissed_alert_ids.clear()

    def evaluate(
        self,
        quarantined_count: int = 0,
        lockdown_enabled: bool = False,
        now: Optional[datetime] = None,
    ) -> tuple[SecurityPosture, List[AnomalyAlert]]:
        current_time = now or datetime.now(timezone.utc)
        cutoff_time = current_time - timedelta(minutes=self.window_minutes)
        cutoff_iso = cutoff_time.isoformat()

        events: List[Dict[str, Any]] = []
        if self.sink:
            try:
                raw_events = self.sink.query_events(limit=300)
                # Filter to events in sliding window
                for evt in raw_events:
                    occ = evt.get("occurred_at")
                    if occ and occ >= cutoff_iso:
                        events.append(evt)
            except Exception:
                events = []

        alerts: List[AnomalyAlert] = []
        failed_auths = 0

        # Heuristic 1: Failed auth grouping by IP and target actor
        ip_failed_auths: Dict[str, int] = {}
        actor_failed_auths: Dict[str, int] = {}

        # Heuristic 2: Route enumeration (404/403 scan)
        ip_route_scans: Dict[str, int] = {}

        for evt in events:
            etype = evt.get("event_type")
            actor_type = evt.get("actor_type")
            source_ip = evt.get("source_ip")
            actor_id = evt.get("actor_id")
            status_code = evt.get("status_code")
            outcome = evt.get("outcome")

            # Check Break-Glass Invocation
            if actor_type == "break_glass":
                alerts.append(
                    AnomalyAlert(
                        rule="break_glass",
                        title="Emergency Break-Glass Invocation",
                        description=f"Action executed via emergency break-glass credentials (IP: {source_ip or 'local'})",
                        severity="critical",
                        source_ip=source_ip,
                        target_actor=actor_id,
                        timestamp=evt.get("occurred_at", current_time.isoformat()),
                        metadata={"operation_id": evt.get("operation_id")},
                    )
                )

            # Check Authentication Failures
            if etype in ("auth.failure", "websocket.auth.failure") or outcome == "denied":
                failed_auths += 1
                if source_ip:
                    ip_failed_auths[source_ip] = ip_failed_auths.get(source_ip, 0) + 1
                if actor_id:
                    actor_failed_auths[actor_id] = actor_failed_auths.get(actor_id, 0) + 1

            # Check Route Scanning
            if status_code in (403, 404):
                if source_ip:
                    ip_route_scans[source_ip] = ip_route_scans.get(source_ip, 0) + 1

            # Check Failed Admin Mutations
            if etype == "admin.action" and outcome in ("failed", "vetoed"):
                alerts.append(
                    AnomalyAlert(
                        rule="admin_failure",
                        title="Failed Administrative Mutation",
                        description=f"Mutating admin command '{evt.get('operation_id') or 'unknown'}' failed or was vetoed",
                        severity="high",
                        source_ip=source_ip,
                        target_actor=actor_id,
                        timestamp=evt.get("occurred_at", current_time.isoformat()),
                        metadata={"reason": evt.get("reason_code")},
                    )
                )

        # Trigger alerts for Brute-Force IP thresholds (>= 5 failures)
        for ip, count in ip_failed_auths.items():
            if count >= 5:
                alerts.append(
                    AnomalyAlert(
                        rule="brute_force_ip",
                        title="Brute Force Credential Spike (IP)",
                        description=f"Detected {count} authentication failures originating from source IP {ip}",
                        severity="high",
                        source_ip=ip,
                        timestamp=current_time.isoformat(),
                        metadata={"count": count},
                    )
                )

        # Trigger alerts for Targeted Username thresholds (>= 5 failures)
        for act, count in actor_failed_auths.items():
            if count >= 5:
                alerts.append(
                    AnomalyAlert(
                        rule="brute_force_user",
                        title="Targeted Account Attack",
                        description=f"Detected {count} failed login attempts targeting account '{act}'",
                        severity="high",
                        target_actor=act,
                        timestamp=current_time.isoformat(),
                        metadata={"count": count},
                    )
                )

        # Trigger alerts for Route Scanning (>= 10 scanning probes)
        for ip, count in ip_route_scans.items():
            if count >= 10:
                alerts.append(
                    AnomalyAlert(
                        rule="route_enumeration",
                        title="API Endpoint Enumeration Scan",
                        description=f"Detected {count} denied or not-found probes from source IP {ip}",
                        severity="medium",
                        source_ip=ip,
                        timestamp=current_time.isoformat(),
                        metadata={"count": count},
                    )
                )

        # Filter out dismissed alerts
        active_alerts = [a for a in alerts if a.alert_id not in self._dismissed_alert_ids]

        # Calculate composite threat index (0 to 100)
        base_score = 5
        for a in active_alerts:
            if a.severity == "critical":
                base_score += 35
            elif a.severity == "high":
                base_score += 20
            elif a.severity == "medium":
                base_score += 10
            elif a.severity == "low":
                base_score += 5

        base_score += min(25, failed_auths * 2)
        threat_index = min(100, max(0, base_score))

        # Classification
        if lockdown_enabled:
            classification = "LOCKDOWN"
        elif threat_index >= 75:
            classification = "CRITICAL"
        elif threat_index >= 45:
            classification = "HIGH"
        elif threat_index >= 20:
            classification = "ELEVATED"
        else:
            classification = "NORMAL"

        posture = SecurityPosture(
            threat_index=threat_index,
            classification=classification,
            failed_auths_15m=failed_auths,
            active_alerts_count=len(active_alerts),
            quarantined_ips_count=quarantined_count,
            lockdown_enabled=lockdown_enabled,
            evaluated_at=current_time.isoformat(),
        )

        return posture, active_alerts
