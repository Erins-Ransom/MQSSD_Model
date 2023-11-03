#include <unistd.h>
#include <iostream>
#include <random>

#include "rocksdb/db.h"

template<typename T>
std::vector<rocksdb::Slice> generateValues(const std::vector<T>& keys);

void printCompactionAndDBStats(rocksdb::DB* db);
void printLSM(rocksdb::DB* db);
void flushMemTable(rocksdb::DB* db);
void waitForBGCompactions(rocksdb::DB* db);