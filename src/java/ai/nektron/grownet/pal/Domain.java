package ai.nektron.grownet.pal;

import java.util.Iterator;

/**
 * Deterministic domain — must iterate items in a stable order.
 */
public interface Domain<T> extends Iterable<T> {
  @Override
  Iterator<T> iterator();
}

