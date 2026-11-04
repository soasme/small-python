/* A native module whose init is named for another module. */
#include "spy-module.h"

SPY_MODULE int spy_init_other(SPYContext *c, SPYValue *module) {
    (void)c; (void)module;
    return 0;
}
