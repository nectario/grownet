package ai.nektron.grownet.pal;

import java.util.Iterator;
import java.util.NoSuchElementException;

public final class IndexDomain implements Domain<Integer> {
  private final int count;
  public IndexDomain(int count) { this.count = Math.max(0, count); }

  @Override
  public Iterator<Integer> iterator() {
    return new Iterator<Integer>() {
      private int current = 0;
      @Override public boolean hasNext() { return current < count; }
      @Override public Integer next() {
        if (!hasNext()) throw new NoSuchElementException();
        return current++;
      }
    };
  }
}

