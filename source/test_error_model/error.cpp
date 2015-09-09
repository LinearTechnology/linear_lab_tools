#include "error.h"
#undef ENUM_START
#define ENUM_START const string Dc1371Error::strings[NUM_ERRORS] = {
#undef ENUM
#define ENUM(name, value) #name
ENUM_DECLARATION;