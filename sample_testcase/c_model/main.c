#include <stdio.h>
#include <stdlib.h>

int main() {
    int a, b;
    // Simple C-model that reads two integers
    if (scanf("%d", &a) != 1) return 1;
    if (scanf("%d", &b) != 1) return 1;
    
    int sum = a + b;
    
    // Write out the inputs first, then the expected output
    // so the testbench can read them all from the golden file
    printf("%d\n", a);
    printf("%d\n", b);
    printf("%d\n", sum);
    
    return 0;
}
