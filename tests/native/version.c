/* A native module linked by hand, built for the spy version BUILT, whose
 * init is INIT. */
#include "spy-module.h"

SPY_EXPORT SPYModuleLink spy_module = {BUILT, NULL};

SPY_EXPORT int INIT(SPYContext *c, SPYValue *module);
SPY_EXPORT int INIT(SPYContext *c, SPYValue *module) {
    (void)c; (void)module;
    return 0;
}
