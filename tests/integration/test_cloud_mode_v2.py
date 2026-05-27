"""Cloud mode v2 tests."""

from core.federation_manager import FederationManager
from core.routing_manager import RoutingManager


def test_cloud_mode_v2_domains_regions_failover_and_summary():
    """Federation manager should route by simulated domains."""
    federation = FederationManager("c1", "eu")
    federation.receive_state({"cluster_id": "c2", "domain": "us", "region": "use1", "status": "ok"})
    federation.receive_state({"cluster_id": "c3", "domain": "eu", "region": "euw1", "status": "backup"})
    router = RoutingManager(federation)
    assert router.route_across_clusters({"domain": "us"})["cluster_id"] == "c2"
    assert router.route_across_clusters({"domain": "eu"})["cluster_id"] == "c3"
    assert federation.heartbeat()["domain"] == "eu"
