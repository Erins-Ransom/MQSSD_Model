#include "rocksdb/db.h"
#include "rocksdb/options.h"

#include "mqssd_util.h"


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

template<typename T>
std::vector<rocksdb::Slice> generateValues(const std::vector<T>& keys) {
    char value_buf[VAL_SZ];
    std::mt19937_64 e(2017);
    std::uniform_int_distribution<unsigned long long> dist(0, ULLONG_MAX);
    std::vector<rocksdb::Slice> vals;

    for (size_t i = 0; i < keys.size(); i++) {
        setValueBuffer(value_buf, VAL_SZ, e, dist);
        vals.push_back(rocksdb::Slice(value_buf, VAL_SZ));
    }

    return vals;
} 

void printCompactionAndDBStats(rocksdb::DB* db) {
    std::string stats;
    db->GetProperty("rocksdb.stats", &stats);
    printf("%s", stats.c_str());
}

void printLSM(rocksdb::DB* db) {
    std::cout << "Print LSM" << std::endl;
    rocksdb::ColumnFamilyMetaData cf_meta;
    db->GetColumnFamilyMetaData(&cf_meta);

    std::cout << "Total Size (bytes): " << cf_meta.size << std::endl;
    std::cout << "Total File Count: " << cf_meta.file_count << std::endl;

    int largest_used_level = -1;
    for (auto level : cf_meta.levels) {
        if (level.files.size() > 0) {
            largest_used_level = level.level;
        }
    }

    std::cout << "Largest Level: " << largest_used_level << std::endl;
    for (auto level : cf_meta.levels) {
        long level_size = 0;
        for (auto file : level.files) {
            level_size += file.size;
        }
        std::cout << "level " << level.level << ".  Size " << level_size << " bytes" << std::endl;
        std::cout << std::endl;
        for (auto file : level.files) {
            std::cout << " \t " << file.size << " bytes \t " << file.name << std::endl;
        }
        if (level.level == largest_used_level) {
            break;
        }
    }

    std::cout << std::endl;
}

void flushMemTable(rocksdb::DB* db) {
    rocksdb::FlushOptions flush_opt;
    flush_opt.wait = true;
    rocksdb::Status s = db->Flush(flush_opt);
    assert(s.ok());
}

void waitForBGCompactions(rocksdb::DB* db) {
    bool double_checked = false;
    uint64_t prop;
    while (true) {
        // Check stats every 10s  
        sleep(10);
        
        if (!(db->GetIntProperty("rocksdb.num-running-flushes", &prop))) continue;
        if (prop > 0) continue;
        if (!(db->GetIntProperty("rocksdb.num-running-compactions", &prop))) continue;
        if (prop > 0) continue;
        if (!(db->GetIntProperty("rocksdb.mem-table-flush-pending", &prop))) continue;
        if (prop == 1) continue;
        if (!(db->GetIntProperty("rocksdb.compaction-pending", &prop))) continue;
        if (prop == 1) continue;

        if (double_checked) {
            break;
        } else {
            double_checked = true;
            continue;
        }
    }

    // Print out initial LSM state
    printLSM(db);
}
