# Validates that we use explicit copy() for containers.
fn test_list_copy_shallow() -> Bool:
    var a = [ [1.0, 2.0], [3.0, 4.0] ]
    var b = a.copy()           # explicit copy of outer list
    a.append([5.0, 6.0])
    # b should not grow when a grows (outer list is independent)
    if b.len != 2: return False
    # shallow copy note: inner rows are references; modifying an element reflects in both
    a[0][0] = 9.0
    if b[0][0] != 9.0:
        # This would fail if list.copy() were deep; expected to pass (shallow).
        return False
    return True
