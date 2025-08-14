#pragma once
namespace grownet {
class RegionBus {
public:
    void setInhibitionFactor(double f) { inhibitionFactor = f; }
    void setModulationFactor(double f) { modulationFactor = f; }
    double getInhibitionFactor() const { return inhibitionFactor; }
    double getModulationFactor() const { return modulationFactor; }
    void decay() { inhibitionFactor *= 0.9; modulationFactor = 1.0; }
    long long getCurrentStep() const { return step; }
    void nextStep() { ++step; decay(); }
private:
    double inhibitionFactor { 0.0 };
    double modulationFactor { 1.0 };
    long long step { 0 };
};
} // namespace grownet
