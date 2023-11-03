#include "rocksdb/db.h"
#include "rocksdb/options.h"
#include "rocksdb/table.h"
#include "rocksdb/statistics.h"
#include "rocksdb/perf_context.h"
#include "rocksdb/iostats_context.h"

#include <iostream>
#include <vector>

#include "mqssd_util.h"

#define INIT_EXP_TIMER auto start = std::chrono::high_resolution_clock::now();  
#define START_EXP_TIMER start = std::chrono::high_resolution_clock::now();  
#define STOP_EXP_TIMER(name)  std::cout << "RUNTIME of " << name << ": " << \
                              std::chrono::duration_cast<std::chrono::microseconds>( \
                                  std::chrono::high_resolution_clock::now() - start \
                              ).count() << " us " << std::endl;


void init(rocksdb::DB** db,
          rocksdb::Options* options, 
          rocksdb::BlockBasedTableOptions* table_options) {
	
    options->create_if_missing = true;
    options->statistics = rocksdb::CreateDBStatistics();

    // Default scaled up by 4
    options->write_buffer_size = 4 * 64 * 1048576;          // Size of memtable = Size of SST file (256 MB) 
    options->max_bytes_for_level_base = 4 * 256 * 1048576;  // 4 SST files at L1
    options->target_file_size_base = 4 * 64 * 1048576;      // Each SST file is 256 MB

    // Force L0 to be empty for consistent LSM tree shape
    options->level0_file_num_compaction_trigger = 1;

    table_options->block_cache = rocksdb::NewLRUCache(1024 * 1024 * 1024); // 1 GB Block Cache

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

    // Enable compression -> more keys per SST file = ?
    // Don't compress first few levels and use better but slower compression at deeper levels
    // options->num_levels = 4;
    // options->compression_per_level.resize(options->num_levels);
    // for (int i = 0; i < options->num_levels; ++i) {
    //     if (i < 2) {
    //         options->compression_per_level[i] = rocksdb::CompressionType::kNoCompression;
    //     } else if (i == 2) {
    //         options->compression_per_level[i] = rocksdb::CompressionType::kLZ4Compression;
    //     } else {
    //         options->compression_per_level[i] = rocksdb::CompressionType::kZSTD;
    //     }
    // }

    /* 
        // By default, RocksDB uses only one background thread for flush and
        // compaction. Calling this function will set it up such that total of
        // `total_threads` is used. Good value for `total_threads` is the number of
        // cores. You almost definitely want to call this function if your system is
        // bottlenecked by RocksDB.
    */
    options->IncreaseParallelism(6);
    
    options->table_factory.reset(rocksdb::NewBlockBasedTableFactory(*table_options));

    // Open database
    const std::string db_path = "./db/";
    rocksdb::Status status = rocksdb::DB::Open(*options, db_path, db);
    assert(status.ok());
}


void loadInitialKeysIntoDB(rocksdb::DB* db, const std::vector<std::string>& keys, const std::vector<rocksdb::Slice>& vals) {
    rocksdb::WriteOptions write_options = rocksdb::WriteOptions();
    rocksdb::Status s;

    // Use RocksDB Put to get "normal" LSM tree shape (all levels populated somewhat)
    for (size_t i = 0; i < keys.size(); i++) {
        s = db->Put(write_options, rocksdb::Slice(keys[i]), vals[i]);
        if (!s.ok()) {
            std::cout << s.ToString().c_str() << "\n";
            assert(false);
        }
    }
}


void warmCache(rocksdb::DB* db,
               const std::vector<std::string>& keys, 
               size_t sample_gap) {

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


int main(int argc, char** argv) {

    INIT_EXP_TIMER

    // Configure and initialize database
    rocksdb::DB* db;
    rocksdb::Options options;
    rocksdb::BlockBasedTableOptions table_options;
    init(&db, &options, &table_options);

    std::vector<std::string> keys;
    auto vals = generateValues(keys);

    START_EXP_TIMER
    loadInitialKeysIntoDB(db, keys, vals);
    STOP_EXP_TIMER("Load Keys into DB")

    START_EXP_TIMER
    flushMemTable(db);
    STOP_EXP_TIMER("Flush MemTable")

    START_EXP_TIMER
    waitForBGCompactions(db);
    STOP_EXP_TIMER("Wait for Background Compactions")

    START_EXP_TIMER
    warmCache(db, keys, keys.size() / 1000000);
    STOP_EXP_TIMER("Cache Warming")

    printCompactionAndDBStats(db);

    // Reset performance stats
    rocksdb::SetPerfLevel(rocksdb::PerfLevel::kEnableTimeAndCPUTimeExceptForMutex);
    rocksdb::get_perf_context()->Reset();
    rocksdb::get_perf_context()->ClearPerLevelPerfContext();
    rocksdb::get_perf_context()->EnablePerLevelPerfContext();
    rocksdb::get_iostats_context()->Reset();
    
    return 0;
}