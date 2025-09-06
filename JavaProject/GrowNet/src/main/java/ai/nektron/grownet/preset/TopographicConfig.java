package ai.nektron.grownet.preset;

public final class TopographicConfig {
    public int kernelH = 7, kernelW = 7;
    public int strideH = 1, strideW = 1;
    public String padding = "same"; // same | valid
    public boolean feedback = false;
    public String weightMode = "gaussian"; // gaussian | dog
    public double sigmaCenter = 2.0;
    public double sigmaSurround = 4.0;
    public double surroundRatio = 0.5;
    public boolean normalizeIncoming = true;

    public TopographicConfig() {}

    public TopographicConfig setKernel(int h, int w) { this.kernelH = h; this.kernelW = w; return this; }
    public TopographicConfig setStride(int h, int w) { this.strideH = h; this.strideW = w; return this; }
    public TopographicConfig setPadding(String padding) { this.padding = padding; return this; }
    public TopographicConfig setFeedback(boolean feedback) { this.feedback = feedback; return this; }
    public TopographicConfig setWeightMode(String mode) { this.weightMode = mode; return this; }
    public TopographicConfig setSigmaCenter(double v) { this.sigmaCenter = v; return this; }
    public TopographicConfig setSigmaSurround(double v) { this.sigmaSurround = v; return this; }
    public TopographicConfig setSurroundRatio(double v) { this.surroundRatio = v; return this; }
    public TopographicConfig setNormalizeIncoming(boolean v) { this.normalizeIncoming = v; return this; }
}

