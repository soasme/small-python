/* A native module whose init raises, naming the attempt. */
#include "spy-module.h"

#include <stdio.h>

static int attempts;

SPY_MODULE int spy_init_failing(SPYContext *c, SPYValue *module) {
    char message[32];
    (void)module;
    snprintf(message, sizeof(message), "attempt %d", ++attempts);
    spy_error(c, "ValueError", message);
    return -1;
}
