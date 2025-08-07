# hello.mojo
fn fib(n: Int) -> Int:
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)

#entry            # ← program entry-point
fn main():
    print("Hello from Mojo!")
    for i in range(10):
        # no f-strings yet, join with commas
        print("fib(", i, ") = ", fib(i))

