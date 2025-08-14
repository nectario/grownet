#pragma once
// GrowNet C++ — slot selection policy enum
// Mirrors Java SlotConfig.Policy { FIXED, NONUNIFORM, ADAPTIVE }
namespace grownet {
    enum class SlotPolicy { FIXED, NONUNIFORM, ADAPTIVE };
} // namespace grownet
