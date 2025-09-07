// File: src/java/ai/nektron/grownet/policy/ProximityConfig.java
package ai.nektron.grownet.policy;

public final class ProximityConfig {
    public boolean proximityConnectEnabled = false;
    public double proximityRadius = 1.0;
    public String proximityFunction = "STEP"; // "STEP" | "LINEAR" | "LOGISTIC"
    public double linearExponentGamma = 1.0;
    public double logisticSteepnessK = 4.0;
    public int proximityMaxEdgesPerTick = 128;
    public int proximityCooldownTicks = 5;
    public long developmentWindowStart = 0L;
    public long developmentWindowEnd = Long.MAX_VALUE;
    public int stabilizationHits = 3;
    public boolean decayIfUnused = true;
    public int decayHalfLifeTicks = 200;
    // Candidate layers optional; empty means all trainable layers.
    // Use an immutable collection / IntSet in your actual codebase if preferred.
    public int[] candidateLayers = new int[0];
    public boolean recordMeshRulesOnCrossLayer = true;

    public boolean isEnabled() { return proximityConnectEnabled; }
}
