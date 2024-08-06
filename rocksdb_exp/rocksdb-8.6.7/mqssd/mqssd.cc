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
#include <thread>
#include <cstring>

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
static size_t filesize = 32;             // in MB
static size_t nflushthreads;
static size_t ncompthreads;
static size_t fanout;
static bool leveled_compaction;
static bool dynamic_level;


void init(rocksdb::DB** db,
          rocksdb::Options* options, 
          rocksdb::BlockBasedTableOptions* table_options) {
	
    options->create_if_missing = true;
    options->statistics = rocksdb::CreateDBStatistics();

    // Force L0 to be empty for consistent LSM tree shape -- Not sure if we want this anymore (especially for read workloads)
    // I believe similar L0 and L1 sizes are recommended for Leveling, but behaves differently for Universal
    // Moving this outside the  init function
    // options->level0_file_num_compaction_trigger = 1;

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

    // Disable compression for now to minimize noise with the model (LZ4 compression is recommended by RocksDB Wiki)
    options->compression = rocksdb::CompressionType::kNoCompression;

    // Keep files open by default - indexes and filters are pre-loaded if pinned when the cache is warmed
    options->max_open_files = -1;
    
    options->table_factory.reset(rocksdb::NewBlockBasedTableFactory(*table_options));

    // Open database
    const std::string db_path = "./db/";
    rocksdb::Status status = rocksdb::DB::Open(*options, db_path, db);
    assert(status.ok());
}

void warmCache(rocksdb::DB* db) {
    std::ifstream queryFile;
    queryFile.open(DATA_DIR + "/queries/1/" + std::to_string(nqueries) + "/0");

    queryFile.seekg(0, queryFile.end);
    size_t file_len = queryFile.tellg();
    queryFile.seekg(0, queryFile.beg);
    size_t sample_gap = file_len / 1000000;
    sample_gap = std::max(sample_gap, 1UL);

    uint64_t q;
    std::string val;
    uint64_t eight_byte_value;
    rocksdb::ReadOptions read_options = rocksdb::ReadOptions();
    rocksdb::Status s;

    // Get inserted keys at regular intervals
    while (queryFile >> q) {
        s = db->Get(read_options, rocksdb::Slice(uint64ToString(q)), &val);
        if (s.ok()) {
            assert(val.size() >= sizeof(q));
            eight_byte_value = *reinterpret_cast<const uint64_t*>(val.data());
            (void)eight_byte_value;
        }
        queryFile.ignore(8 * sample_gap);
    }
}

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
    keyFile.open(DATA_DIR + "/keys/1/" + std::to_string(nkeys) + "/0");

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
    waitForBGCompactions(db, leveled_compaction);
    printCompactionAndDBStats(db);
}

void runReadWorkload(rocksdb::DB* db) {
    std::ifstream queryFile;
    queryFile.open(DATA_DIR + "/queries/1/" + std::to_string(nqueries) + "/0");

    uint64_t q;
    std::string val;
    uint64_t eight_byte_value;
    rocksdb::ReadOptions read_options = rocksdb::ReadOptions();
    rocksdb::Status s;

    // Get inserted keys at regular intervals
    while (queryFile >> q) {
        s = db->Get(read_options, rocksdb::Slice(uint64ToString(q)), &val);
        if (s.ok()) {
            assert(val.size() >= sizeof(q));
            eight_byte_value = *reinterpret_cast<const uint64_t*>(val.data());
            (void)eight_byte_value;
        }
    }
}

// void runReadWorkloadMultiThreaded(rocksdb::DB* db) {
//     std::vector<std::thread> threads;

//     rocksdb::ReadOptions read_options = rocksdb::ReadOptions();
//     rocksdb::Status s;
//     std::string value_found;
//     uint64_t eight_byte_value;

//     for (size_t i = 0; i < keys.size(); i++) {
//         s = db->Get(read_options, rocksdb::Slice(keys[i]), &value_found);
//         if (s.ok()) {
//             assert(value_found.size() >= sizeof(eight_byte_value));
//             eight_byte_value = *reinterpret_cast<const uint64_t*>(value_found.data());
//             (void)eight_byte_value;
//         }
//     }
// }


int main(int argc, char** argv) {

    INIT_EXP_TIMER

    assert(argc == 10);

    DATA_DIR = argv[1];
    nkeys = strtoull(argv[2], nullptr, 10);
    nqueries = strtoull(argv[3], nullptr, 10);
    nflushthreads = strtoull(argv[4], nullptr, 10);
    ncompthreads = strtoull(argv[5], nullptr, 10);
    fanout = strtoull(argv[6], nullptr, 10);
    leveled_compaction = std::strncmp(argv[7], "Level", 5) == 0;
    dynamic_level = std::strncmp(argv[8], "1", 1) == 0;
    filesize = strtoull(argv[9], nullptr, 10);


    // std::cout << "Data Dir:\t" << DATA_DIR << std::endl;
    // std::cout << "Number of Keys:\t" << nkeys << std::endl;
    // std::cout << "Number of Queries:\t" << nqueries << std::endl;
    // std::cout << "Number of Flush Threads:\t" << nflushthreads << std::endl;
    // std::cout << "Number of Compaction Threads:\t" << ncompthreads << std::endl;
    // std::cout << "Fanout:\t" << fanout << std::endl;
    // std::cout << "Max Subcompactions:\t" << max_subcompactions << std::endl;
    // std::cout << "Leveled Compaction?:\t" << leveled_compaction << std::endl;
    // std::cout << "Dynamic Level?:\t" << dynamic_level << std::endl;

    rocksdb::DB* db;
    rocksdb::Options options;
    rocksdb::BlockBasedTableOptions table_options;
    rocksdb::SetPerfLevel(rocksdb::PerfLevel::kEnableTimeAndCPUTimeExceptForMutex); 

    size_t val_sz = 512;
    size_t num_L1_files = 4;


    // options.num_levels = 9;
    options.write_buffer_size = filesize * 1048576;                                           // Memtable Size (default: 64 MB)
    options.target_file_size_base = filesize * 1048576;                                       // Target SST File Size (default: 64 MB)
    // Number of background threads for flushes and compactions (default: 1)   
    // options.IncreaseParallelism(nthreads);
    /* Default behavior for IncreaseParalelism(total_threads):
         max_background_jobs = total_threads;
         env->SetBackgroundThreads(total_threads, Env::LOW);
         env->SetBackgroundThreads(1, Env::HIGH);               */
    options.max_background_jobs = nflushthreads + ncompthreads;
    options.env->SetBackgroundThreads(nflushthreads, rocksdb::Env::HIGH);
    options.max_background_flushes = nflushthreads;                                     // may not do anything, lol
    options.env->SetBackgroundThreads(ncompthreads, rocksdb::Env::LOW);
    options.max_background_compactions = ncompthreads;                                  // may not do anything, lol
    options.max_subcompactions = ncompthreads;                                          // can override max_background_jobs

    /************************************************************************
     *   options.level0_file_num_compaction_trigger                         *
     ************************************************************************
     *   LEVEL:      Number of L0 files that triggers compaction into L1    *
     *   UNIVERSAL:  Number of TOTAL sorted runs to trigger any compacation *
     ************************************************************************/

    if (leveled_compaction) {
        options.num_levels = 9;
        options.compaction_style = rocksdb::kCompactionStyleLevel;                          // Default Compaction is Tiered+Leveled, only L0 is tiered
        options.level_compaction_dynamic_level_bytes = dynamic_level;
        options.target_file_size_multiplier = 1;                                            // Same SST file size for all levels by default, only implemented for level...?
        options.max_bytes_for_level_base = num_L1_files * options.target_file_size_base;    // Default 4 L1 file
        options.max_bytes_for_level_multiplier = fanout;
        options.level0_file_num_compaction_trigger = num_L1_files;                          // Suggestion is same size for L0 and L1
    } else {

       /*************************************************************************************
        *   UNIVERSAL COMPACTION                                                            *
        *************************************************************************************
        *   PRECONDIDTION:  total sorted runs >= level0_file_num_compaction_trigger         *
        *                                                                                   *
        *              IF:  there are files older than periodic_compaction_seconds,         *
        *                   then compact oldest possible runs into last run                 *
        *                                                                                   *
        *          ELSEIF:  sum(size(Li), i:0-(N-1)) / size(LN) >=                          *
        *                   compaction_options_universal.max_size_amplification_percent,    *
        *                   then perform major compaction (compact all runs to single one)  *
        *                                                                                   * 
        *          ELSEIF:  there is an x for which size(Lx) / sum(size(Li), i:0-(x-1)) <=  *
        *                   (100 + compaction_options_universal.size_ratio) / 100, compact  *
        *                   runs 0-x for the largest such x                                 *
        *                                                                                   * 
        *            ELSE:  try to schedule minor compaction without respecting ratio...    *
        *                   it is unclear when this succeeds?                               *
        *                                                                                   * 
        *            ALSO:  compaction_options_universal.min_merge_width &                  *
        *                   compaction_options_universal.max_merge_width determine min and  *
        *                   max number of input runs for compaction respectively            *
        *                                                                                   *
        *            NOTE:  The settings below should theoretically get behavior similar to *
        *                   standard tiering                                                *
        *                                                                                   *
        *         EXAMPLE:  settings from below, file size = 1, fanout = 4                  *
        *                                                                                   *
        *                   1 (flush)                                                       *
        *                   1 1 (flush)                                                     *
        *                   1 1 1 (flush)                                                   *
        *                   1 1 1 1 (flush, file trigger)                                   *
        *                   4 (major compaction)                                            *
        *                   1 4 (flush)                                                     *
        *                   1 1 4 (flush)                                                   *
        *                   1 1 1 4 (flush, file trigger, but no valid candidates)          *
        *                   1 1 1 1 4 (flush)                                               *
        *                   4 4 (minor compaction)                                          *
        *                   1 4 4 (flush)                                                   *
        *                   1 1 4 4 (flush, file trigger, but no valid candidates)          *
        *                   1 1 1 4 4 (flush)                                               *
        *                   1 1 1 1 4 4 (flush)                                             *
        *                   4 4 4 (minor compaction)                                        *
        *                   1 4 4 4 (flush, file trigger, but no valid candidates)          *
        *                   1 1 4 4 4 (flush)                                               *
        *                   1 1 1 4 4 4 (flush)                                             *
        *                   1 1 1 1 4 4 4 (flush)                                           *
        *                   4 4 4 4 (minor compaction)                                      *
        *                   16 (major compaction)                                           *
        *                   1 16 (flush)                                                    *
        *                   1 1 16 (flush)                                                  *
        *                   1 1 1 16 (flush, file trigger, but no valid candidates)         *
        *                   1 1 1 1 16 (flush)                                              *
        *                   4 16 (minor compaction)                                         *
        *                   etc.                                                            *
        *                                                                                   *
        *************************************************************************************/


        options.num_levels = fanout * 5;                                                // each run is stored as a "level" except those in L0
        options.compaction_style = rocksdb::kCompactionStyleUniversal;                  // Universal ~= Tiered
        options.periodic_compaction_seconds = 0;                                        // 0: disabled, default: 30 days
        options.level0_file_num_compaction_trigger = fanout;         
        options.compaction_options_universal.max_size_amplification_percent =           // default: 200
                100 * ((fanout - 1) + fanout / (fanout - 1));                           // full tree as percent of largest run 
        options.compaction_options_universal.size_ratio = 1;                            // default: 1
        options.compaction_options_universal.min_merge_width = fanout;                  // default: 2
        options.compaction_options_universal.max_merge_width = fanout;                  // default: UINT_MAX
        
    }


    init(&db, &options, &table_options);

    START_EXP_TIMER
    runWriteWorkload(db, val_sz);
    STOP_EXP_TIMER("Write Workload")

    printStats(db, &options);

    // Reset performance stats -- Move this after cache warming?
    // rocksdb::get_perf_context()->Reset();
    // rocksdb::get_perf_context()->ClearPerLevelPerfContext();
    // rocksdb::get_perf_context()->EnablePerLevelPerfContext();
    // rocksdb::get_iostats_context()->Reset();


    // only do read workload for one thread count
    if (ncompthreads == 1)
    {
        START_EXP_TIMER
        warmCache(db);
        STOP_EXP_TIMER("Warm Cache")

        rocksdb::get_perf_context()->Reset();
        rocksdb::get_perf_context()->ClearPerLevelPerfContext();
        rocksdb::get_perf_context()->EnablePerLevelPerfContext();
        rocksdb::get_iostats_context()->Reset();

        START_EXP_TIMER
        runReadWorkload(db);
        STOP_EXP_TIMER("Read Workload")

        printStats(db, &options);
    }
    // Close database
    rocksdb::Status s = db->Close();
    assert(s.ok());
    delete db;

    return 0;
}