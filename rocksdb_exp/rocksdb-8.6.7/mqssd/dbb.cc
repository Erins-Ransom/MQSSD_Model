#include "rocksdb/db.h"
#include "rocksdb/options.h"
#include "rocksdb/table.h"
#include "rocksdb/statistics.h"


static size_t filesize;
static size_t nflushthreads = 1;
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


int main(int argc, char** argv) {
    assert(argc == 6);

    ncompthreads = strtoull(argv[1], nullptr, 10);
    fanout = strtoull(argv[2], nullptr, 10);
    leveled_compaction = std::strncmp(argv[3], "Level", 5) == 0;
    dynamic_level = std::strncmp(argv[4], "1", 1) == 0;
    filesize = strtoull(argv[5], nullptr, 10);

    rocksdb::DB* db;
    rocksdb::Options options;
    rocksdb::BlockBasedTableOptions table_options;
    // rocksdb::SetPerfLevel(rocksdb::PerfLevel::kEnableTimeAndCPUTimeExceptForMutex);

    options.write_buffer_size = filesize * 1048576;                                           // Memtable Size (default: 64 MB)
    options.target_file_size_base = filesize * 1048576;                              // Target SST File Size (default: 64 MB)

    /* 
        Default behavior for IncreaseParalelism(total_threads):
         max_background_jobs = total_threads;
         env->SetBackgroundThreads(total_threads, Env::LOW);
         env->SetBackgroundThreads(1, Env::HIGH);               
    */
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
        size_t num_L1_files = 4;
        options.num_levels = 9;
        options.compaction_style = rocksdb::kCompactionStyleLevel;                          // Default Compaction is Tiered+Leveled, only L0 is tiered
        options.level_compaction_dynamic_level_bytes = dynamic_level;
        options.target_file_size_multiplier = 1;                                            // Same SST file size for all levels by default, only implemented for level...?
        options.max_bytes_for_level_base = num_L1_files * options.target_file_size_base;    // Default 4 L1 file
        options.max_bytes_for_level_multiplier = fanout;
        options.level0_file_num_compaction_trigger = num_L1_files;                          // Suggestion is same size for L0 and L1
    } else {
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

    // Close database
    rocksdb::Status s = db->Close();
    assert(s.ok());
    delete db;

    return 0;
}