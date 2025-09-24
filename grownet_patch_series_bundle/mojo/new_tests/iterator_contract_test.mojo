# Iterators return references; there is no need to dereference with [].
fn test_iterator_reference() -> Bool:
    var xs = [1, 2, 3]
    var s = 0
    for e in xs:
        s = s + e
    return s == 6
