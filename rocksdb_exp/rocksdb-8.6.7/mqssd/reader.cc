#include "rocksdb/db.h"
#include "rocksdb/options.h"
#include "rocksdb/table.h"
#include "rocksdb/statistics.h"
#include "rocksdb/perf_context.h"
#include "rocksdb/iostats_context.h"

#include <cassert>
#include <cstdlib>
#include <string>
#include <fstream>
#include <iostream>

#include "mqssd_util.h"


static const std::string DB_PATH = "./db/";
static std::string QUERY_FILE_PATH;

int main(int argc, char** argv) {
    assert(argc == 2);

    QUERY_FILE_PATH = argv[1];

    printf("%s\n", QUERY_FILE_PATH.c_str());

    rocksdb::DB* db;
    rocksdb::Options options;
    rocksdb::Status s = rocksdb::DB::OpenForReadOnly(options, DB_PATH, &db);
    assert(s.ok() && db);
    
    std::ifstream queryFile;
    queryFile.open(QUERY_FILE_PATH);

    rocksdb::ReadOptions read_options = rocksdb::ReadOptions();
    uint64_t q;
    std::string value;
    
    uint64_t count = 0;

    while (queryFile >> q) {
        s = db->Get(read_options, rocksdb::Slice(uint64ToString(q)), &value);
        if (!s.ok()) {
            std::cout << s.ToString().c_str() << "\n";
            assert(false);
        }
        count++;
    }

}