#include <unistd.h>
#include <iostream>
#include <random>

#include "rocksdb/db.h"

std::string uint64ToString(const uint64_t word);

std::vector<rocksdb::Slice> generateValues(const std::vector<std::string>& keys, size_t val_sz);

void printCompactionAndDBStats(rocksdb::DB* db);
void printLSM(rocksdb::DB* db);
void flushMemTable(rocksdb::DB* db);
void waitForBGCompactions(rocksdb::DB* db);
void printStats(rocksdb::DB* db,
                rocksdb::Options* options);