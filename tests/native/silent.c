/* A native module whose init fails without raising. */
#include "spy-module.h"

SPY_MODULE int spy_init_silent(SPYContext *c, SPYValue *module) {
    (void)c; (void)module;
    return -1;
}
