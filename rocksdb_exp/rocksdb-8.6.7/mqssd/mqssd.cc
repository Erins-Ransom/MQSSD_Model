#include "rocksdb/db.h"
#include "rocksdb/options.h"
#include "rocksdb/table.h"
#include "rocksdb/statistics.h"
#include "rocksdb/perf_context.h"
#include "rocksdb/iostats_context.h"

#include <iostream>
#include <fstream>
#include <vector>
#include <random>

#include "mqssd_util.h"

#define INIT_EXP_TIMER auto start = std::chrono::high_resolution_clock::now();  
#define START_EXP_TIMER start = std::chrono::high_resolution_clock::now();  
#define STOP_EXP_TIMER(name)  std::cout << "RUNTIME of " << name << ": " << \
                              std::chrono::duration_cast<std::chrono::microseconds>( \
                                  std::chrono::high_resolution_clock::now() - start \
                              ).count() << " us " << std::endl;


static std::string DATA_DIR;
static size_t nkeys;
static size_t nqueries;
static size_t nthreads;
static size_t fanout;


void init(rocksdb::DB** db,
          rocksdb::Options* options, 
          rocksdb::BlockBasedTableOptions* table_options) {
	
    options->create_if_missing = true;
    options->statistics = rocksdb::CreateDBStatistics();

    // Force L0 to be empty for consistent LSM tree shape
    options->level0_file_num_compaction_trigger = 1;

    // 1 GB Block Cache
    table_options->block_cache = rocksdb::NewLRUCache(1024 * 1024 * 1024);

    // higher read-ahead generally recommended for disks, 
    // for flash/ssd generally 0 is ok, as can unnecessarily 
    // cause extra read-amp on smaller compactions
    options->compaction_readahead_size = 0;

    table_options->partition_filters = false;

    // no mmap for reads nor writes
    options->allow_mmap_reads = false;
    options->allow_mmap_writes = false;

    // direct I/O usage points
    options->use_direct_reads = true;
    options->use_direct_io_for_flush_and_compaction = true;

    // Use LZ4 compression as recommended by RocksDB Wiki
    options->compression = rocksdb::CompressionType::kLZ4Compression;

    // Keep files open by default - indexes and filters are pre-loaded if pinned when the cache is warmed
    options->max_open_files = -1;
    
    options->table_factory.reset(rocksdb::NewBlockBasedTableFactory(*table_options));

    // Open database
    const std::string db_path = "./db/";
    rocksdb::Status status = rocksdb::DB::Open(*options, db_path, db);
    assert(status.ok());
}

void warmCache(rocksdb::DB* db,
               const std::vector<std::string>& keys, 
               size_t sample_gap) {
    
    sample_gap = std::max(sample_gap, 1UL);

    rocksdb::ReadOptions read_options = rocksdb::ReadOptions();
    rocksdb::Status s;
    std::string value_found;
    uint64_t eight_byte_value;

    // Get inserted keys at regular intervals
    for (size_t i = 0; i < keys.size(); i += sample_gap) {
        s = db->Get(read_options, rocksdb::Slice(keys[i]), &value_found);
        if (s.ok()) {
            assert(value_found.size() >= sizeof(eight_byte_value));
            eight_byte_value = *reinterpret_cast<const uint64_t*>(value_found.data());
            (void)eight_byte_value;
        }
    }
}

// std::vector<std::string> generateKeys(size_t nkeys) {
//     std::vector<std::string> keys;
//     keys.reserve(nkeys);

//     std::random_device rd;  // Will be used to obtain a seed for the random number engine
//     std::mt19937_64 gen(rd()); // Standard mersenne_twister_engine seeded with rd()
//     std::uniform_int_distribution<uint64_t> uni_dist(0, std::numeric_limits<uint64_t>::max());

//     while (keys.size() < nkeys) {
//         uint64_t number = uni_dist(gen);
//         keys.push_back(uint64ToString(number));
//     }

//     return keys;
// }

// assume compression ratio = 0.5
void setValueBuffer(char* value_buf, int size,
		            std::mt19937_64 &e,
		            std::uniform_int_distribution<unsigned long long>& dist) {
    memset(value_buf, 0, size);
    int pos = size / 2;
    while (pos < size) {
        uint64_t num = dist(e);
        char* num_bytes = reinterpret_cast<char*>(&num);
        memcpy(value_buf + pos, num_bytes, 8);
        pos += 8;
    }
}

void runWriteWorkload(rocksdb::DB* db, size_t val_sz) {
    std::ifstream keyFile;
    keyFile.open(DATA_DIR + "/keys/" + std::to_string(nkeys) + ".txt");

    uint64_t key;
    rocksdb::WriteOptions write_options = rocksdb::WriteOptions();
    rocksdb::Status s;
    char value_buf[val_sz];
    std::mt19937_64 e(2024);
    std::uniform_int_distribution<unsigned long long> dist(0, ULLONG_MAX);

    while (keyFile >> key) {
        setValueBuffer(value_buf, val_sz, e, dist);
        s = db->Put(write_options, rocksdb::Slice(uint64ToString(key)), rocksdb::Slice(value_buf, val_sz));
        if (!s.ok()) {
            std::cout << s.ToString().c_str() << "\n";
            assert(false);
        }
    }

    flushMemTable(db);
    waitForBGCompactions(db);
    printCompactionAndDBStats(db);
}


void runReadWorkload(rocksdb::DB* db, const std::vector<std::string>& keys) {
    rocksdb::ReadOptions read_options = rocksdb::ReadOptions();
    rocksdb::Status s;
    std::string value_found;
    uint64_t eight_byte_value;

    for (size_t i = 0; i < keys.size(); i++) {
        s = db->Get(read_options, rocksdb::Slice(keys[i]), &value_found);
        if (s.ok()) {
            assert(value_found.size() >= sizeof(eight_byte_value));
            eight_byte_value = *reinterpret_cast<const uint64_t*>(value_found.data());
            (void)eight_byte_value;
        }
    }
}


int main(int argc, char** argv) {

    INIT_EXP_TIMER

    assert (argc == 6);

    DATA_DIR = argv[1];
    nkeys = strtoull(argv[2], nullptr, 10);
    nqueries = strtoull(argv[3], nullptr, 10);
    nthreads = strtoull(argv[4], nullptr, 10);
    fanout = strtoull(argv[5], nullptr, 10);

    rocksdb::DB* db;
    rocksdb::Options options;
    rocksdb::BlockBasedTableOptions table_options;
    rocksdb::SetPerfLevel(rocksdb::PerfLevel::kEnableTimeAndCPUTimeExceptForMutex); 

    size_t val_sz = 512;
    size_t num_L1_files = 4;

    options.num_levels = 5;

    // options.level_compaction_dynamic_level_bytes = false;

    options.compaction_style = rocksdb::kCompactionStyleLevel;                          // Default Compaction is Tiered+Leveled.

    options.write_buffer_size = 32 * 1048576;                                           // Memtable Size (default: 64 MB)
    options.target_file_size_base = 32 * 1048576;                                       // Target SST File Size (default: 64 MB)
    options.max_bytes_for_level_base = num_L1_files * options.target_file_size_base;    // Default 4 L1 files

    options.target_file_size_multiplier = 1;                                            // Same SST file size for all levels by default
    options.max_bytes_for_level_multiplier = fanout;                                    // Default fanout is 10

    // Number of background threads for flushes and compactions (default: 1)   
    options.IncreaseParallelism(nthreads);

    init(&db, &options, &table_options);

    START_EXP_TIMER
    runWriteWorkload(db, val_sz);
    STOP_EXP_TIMER("Write Workload")

    printStats(db, &options);

    // Reset performance stats
    rocksdb::get_perf_context()->Reset();
    rocksdb::get_perf_context()->ClearPerLevelPerfContext();
    rocksdb::get_perf_context()->EnablePerLevelPerfContext();
    rocksdb::get_iostats_context()->Reset();

    // START_EXP_TIMER
    // warmCache(db, keys, keys.size() / 1000000);
    // STOP_EXP_TIMER("Warm Cache")
    
    // START_EXP_TIMER
    // runReadWorkload(db);
    // STOP_EXP_TIMER("Read Workload")

    // Close database
    rocksdb::Status s = db->Close();
    assert(s.ok());
    delete db;

    return 0;
}