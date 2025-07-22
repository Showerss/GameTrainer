#include <time.h>
#include "input.h"

int main() {
    srand((unsigned)time(NULL));
    // move with jitter:
    JitteredMouseMove(500, 300);
    // press the “A” key:
    SendKey(0x41);
    return 0;
}
