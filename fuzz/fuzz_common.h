#ifndef FUZZ_COMMON_H
#define FUZZ_COMMON_H

#include <stddef.h>
#include <stdint.h>

#include "spy.h"

/* A context for one input: output discarded, no input, loader, or mounts,
 * and a step budget so loops end. NULL if it cannot be created. */
SPYContext *fuzz_context_new(void);
/* Collect cycles and free the context, so leaks show up per input. */
void fuzz_context_free(SPYContext *);
/* A malloc-allocated, NUL-terminated copy of the fuzzer's bytes. */
char *fuzz_source(const uint8_t *data, size_t size);

#endif
