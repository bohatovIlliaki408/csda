#include <climits>
#include <cassert>

#include "math_operations.h"

void test_add() {
    // Test cases for the add() function

    // Test with positive numbers
    assert(add(2, 3) == 5);
    assert(add(10, 15) == 25);

    // Test with negative numbers
    assert(add(-1, -1) == -2);
    assert(add(-5, 3) == -2);

    // Test with zero
    assert(add(0, 0) == 0);
    assert(add(0, 5) == 5);
    assert(add(5, 0) == 5);

    // Edge cases
    assert(add(INT_MAX, 0) == INT_MAX);
    assert(add(INT_MIN, 0) == INT_MIN);
    assert(add(INT_MAX, 1) == INT_MIN);  // Overflow case
}

int main() {
    test_add();
    return 0;
}
