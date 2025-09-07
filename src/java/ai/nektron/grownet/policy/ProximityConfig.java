package ai.nektron.grownet.policy;

public final class ProximityConfig {
    private boolean enabled = false;
    private double  radius  = 1.0;
    private String  function = "STEP"; // STEP | LINEAR | LOGISTIC
    private double  linearExponentGamma = 1.0;
    private double  logisticSteepnessK  = 4.0;
    private int     maxEdgesPerTick = 128;
    private int     cooldownTicks   = 5;
    private long    developmentWindowStart = 0L;
    private long    developmentWindowEnd   = Long.MAX_VALUE;
    private int     stabilizationHits = 3;
    private boolean decayIfUnused     = true;
    private int     decayHalfLifeTicks = 200;
    private java.util.Set<Integer> candidateLayers = java.util.Collections.emptySet();
    private boolean recordMeshRulesOnCrossLayer = true;

    public boolean isEnabled() { return enabled; }
    public ProximityConfig setEnabled(boolean v) { this.enabled = v; return this; }
    public double getRadius() { return radius; }
    public ProximityConfig setRadius(double v) { this.radius = v; return this; }
    public String getFunction() { return function; }
    public ProximityConfig setFunction(String v) { this.function = v; return this; }
    public double getLinearExponentGamma() { return linearExponentGamma; }
    public ProximityConfig setLinearExponentGamma(double v) { this.linearExponentGamma = v; return this; }
    public double getLogisticSteepnessK() { return logisticSteepnessK; }
    public ProximityConfig setLogisticSteepnessK(double v) { this.logisticSteepnessK = v; return this; }
    public int getMaxEdgesPerTick() { return maxEdgesPerTick; }
    public ProximityConfig setMaxEdgesPerTick(int v) { this.maxEdgesPerTick = v; return this; }
    public int getCooldownTicks() { return cooldownTicks; }
    public ProximityConfig setCooldownTicks(int v) { this.cooldownTicks = v; return this; }
    public long getDevelopmentWindowStart() { return developmentWindowStart; }
    public ProximityConfig setDevelopmentWindowStart(long v) { this.developmentWindowStart = v; return this; }
    public long getDevelopmentWindowEnd() { return developmentWindowEnd; }
    public ProximityConfig setDevelopmentWindowEnd(long v) { this.developmentWindowEnd = v; return this; }
    public int getStabilizationHits() { return stabilizationHits; }
    public ProximityConfig setStabilizationHits(int v) { this.stabilizationHits = v; return this; }
    public boolean isDecayIfUnused() { return decayIfUnused; }
    public ProximityConfig setDecayIfUnused(boolean v) { this.decayIfUnused = v; return this; }
    public int getDecayHalfLifeTicks() { return decayHalfLifeTicks; }
    public ProximityConfig setDecayHalfLifeTicks(int v) { this.decayHalfLifeTicks = v; return this; }
    public java.util.Set<Integer> getCandidateLayers() { return candidateLayers; }
    public ProximityConfig setCandidateLayers(java.util.Set<Integer> layers) { this.candidateLayers = (layers==null?java.util.Collections.emptySet():layers); return this; }
    public boolean isRecordMeshRulesOnCrossLayer() { return recordMeshRulesOnCrossLayer; }
    public ProximityConfig setRecordMeshRulesOnCrossLayer(boolean v) { this.recordMeshRulesOnCrossLayer = v; return this; }
}

