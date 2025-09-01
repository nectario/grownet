package ai.nektron.grownet.tests;

import ai.nektron.grownet.Layer;
import ai.nektron.grownet.Neuron;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;

/**
 * Tests for Frozen Slots (Java).
 *
 * This test assumes the Frozen Slots API has been added:
 *  - Neuron.freezeLastSlot() / Neuron.unfreezeLastSlot()
 *  - Weight.freeze() / Weight.unfreeze() / Weight.isFrozen()   (or a boolean "frozen" field)
 *
 * It deliberately uses reflection fallbacks so it still compiles even if method names
 * differ slightly; if neither the Neuron nor Weight frozen APIs exist, assertions will fail.
 */
public class FrozenSlotsTest {

    // ---------- small reflection helpers ----------

    private static boolean callFreezeLastSlotIfPresent(Neuron neuron, Object slot) throws Exception {
        try {
            Method m = neuron.getClass().getMethod("freezeLastSlot");
            Object result = m.invoke(neuron);
            return (result instanceof Boolean) ? (Boolean) result : true;
        } catch (NoSuchMethodException e) {
            // Fallback: call Weight.freeze() on the slot
            Method m = slot.getClass().getMethod("freeze");
            m.invoke(slot);
            return true;
        }
    }

    private static boolean callUnfreezeLastSlotIfPresent(Neuron neuron, Object slot) throws Exception {
        try {
            Method m = neuron.getClass().getMethod("unfreezeLastSlot");
            Object result = m.invoke(neuron);
            return (result instanceof Boolean) ? (Boolean) result : true;
        } catch (NoSuchMethodException e) {
            // Fallback: call Weight.unfreeze() on the slot
            Method m = slot.getClass().getMethod("unfreeze");
            m.invoke(slot);
            return true;
        }
    }

    private static boolean isFrozen(Object slot) throws Exception {
        // Try a typical getter first
        try {
            Method m = slot.getClass().getMethod("isFrozen");
            Object v = m.invoke(slot);
            if (v instanceof Boolean) return (Boolean) v;
        } catch (NoSuchMethodException ignore) {}

        // Fallback to a boolean field named "frozen"
        try {
            Field f = slot.getClass().getDeclaredField("frozen");
            f.setAccessible(true);
            return f.getBoolean(slot);
        } catch (NoSuchFieldException e) {
            throw new AssertionError("No Weight.isFrozen() or Weight.frozen field found; did you apply the Frozen Slots PR?");
        }
    }

    private static double getStrength(Object slot) throws Exception {
        // Try common getter names
        for (String name : new String[]{"getStrength", "getStrengthValue"}) {
            try {
                Method m = slot.getClass().getMethod(name);
                Object v = m.invoke(slot);
                return ((Number) v).doubleValue();
            } catch (NoSuchMethodException ignore) {}
        }
        // Fallback to field
        try {
            Field f = slot.getClass().getDeclaredField("strength");
            f.setAccessible(true);
            return ((Number) f.get(slot)).doubleValue();
        } catch (NoSuchFieldException e) {
            throw new AssertionError("No Weight.getStrength[Value]() or Weight.strength found; update test or PR.");
        }
    }

    private static double getTheta(Object slot) throws Exception {
        // Try common getter names
        for (String name : new String[]{"getTheta", "getThreshold", "getThresholdValue"}) {
            try {
                Method m = slot.getClass().getMethod(name);
                Object v = m.invoke(slot);
                return ((Number) v).doubleValue();
            } catch (NoSuchMethodException ignore) {}
        }
        // Fallback to field
        try {
            Field f = slot.getClass().getDeclaredField("theta");
            f.setAccessible(true);
            return ((Number) f.get(slot)).doubleValue();
        } catch (NoSuchFieldException e) {
            throw new AssertionError("No Weight.getTheta()/getThreshold[Value]() or Weight.theta found; update test or PR.");
        }
    }

    // Get the single existing slot after first drive (map is Integer->Weight)
    private static Object getOnlySlot(Neuron neuron) {
        @SuppressWarnings("unchecked")
        Map<Integer, Object> slots = (Map<Integer, Object>) neuron.getSlots();
        assertNotNull(slots, "Neuron.getSlots() returned null");
        assertFalse(slots.isEmpty(), "Neuron has no slots; did you drive it at least once?");
        return slots.values().iterator().next();
    }

    // ---------- tests ----------

    @Test
    public void frozenFlagTogglesOnFreezeUnfreeze() throws Exception {
        // Single-neuron layer for a controlled drive
        Layer layer = new Layer(/*excit*/1, /*inh*/0, /*mod*/0);
        Neuron neuron = layer.getNeurons().get(0);

        // First drive => select/create FIRST-anchor slot
        layer.forward(0.6);
        layer.endTick();

        Object slot = getOnlySlot(neuron);

        // Freeze
        assertTrue(callFreezeLastSlotIfPresent(neuron, slot), "freezeLastSlot()/freeze() failed");
        assertTrue(isFrozen(slot), "Slot should be frozen");

        // Unfreeze
        assertTrue(callUnfreezeLastSlotIfPresent(neuron, slot), "unfreezeLastSlot()/unfreeze() failed");
        assertFalse(isFrozen(slot), "Slot should be unfrozen");
    }

    @Test
    public void frozenStopsAdaptationAndResumesAfterUnfreeze() throws Exception {
        Layer layer = new Layer(/*excit*/1, /*inh*/0, /*mod*/0);
        Neuron neuron = layer.getNeurons().get(0);

        // Establish slot and baseline values
        layer.forward(0.55);
        layer.endTick();
        Object slot = getOnlySlot(neuron);
        double strength0 = getStrength(slot);
        double theta0 = getTheta(slot);

        // Freeze and drive with a value that would normally adapt
        assertTrue(callFreezeLastSlotIfPresent(neuron, slot));
        layer.forward(0.95);
        layer.endTick();

        // While frozen, both strength and theta should remain unchanged
        assertEquals(strength0, getStrength(slot), 1e-12, "Strength should not change while frozen");
        assertEquals(theta0, getTheta(slot), 1e-12, "Theta should not change while frozen");

        // Unfreeze and drive again — adaptation should resume (strength increases)
        assertTrue(callUnfreezeLastSlotIfPresent(neuron, slot));
        layer.forward(0.85);
        layer.endTick();

        assertTrue(getStrength(slot) > strength0, "Strength should increase after unfreeze");
    }
}
