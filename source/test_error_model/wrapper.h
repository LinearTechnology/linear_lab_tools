#pragma once

typedef void* Handle;

Handle Create(bool is_dc1371);
int Cleanup(Handle* handle);
int GetValue(Handle handle, int i, double* value);
int NoValue(Handle handle, bool throw_error);
void GetErrorString(char* buffer, int buffer_size);