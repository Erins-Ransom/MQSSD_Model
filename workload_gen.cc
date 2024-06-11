#include <cassert>
#include <vector>
#include <sstream>
#include <fstream>
#include <iterator>
#include <random>
#include <filesystem>

int main(int argc, char *argv[]) {
    assert(argc == 4);

    const std::string DATA_DIR = argv[1];
    size_t nkeys = atoi(argv[2]);
    size_t nthreads = atoi(argv[3]);
    assert(nthreads > 0);

    assert(std::filesystem::exists(DATA_DIR));
    std::string path = DATA_DIR + "/" + std::to_string(nthreads) + "/" + std::to_string(nkeys);
    std::filesystem::create_directories(path);

    std::random_device rd;  // Will be used to obtain a seed for the random number engine
    std::mt19937_64 gen(rd()); // Standard mersenne_twister_engine seeded with rd()
    std::uniform_int_distribution<uint64_t> uni_dist(0, UINT64_MAX);

    size_t sz = ((nkeys + (nthreads - 1)) / nthreads);
    size_t total = 0;
    for (size_t i = 0; i < nthreads; i++) {
        std::ofstream fout;
        fout.open(path + "/" + std::to_string(i), std::ios::out);
        for (size_t j = 0; j < sz && total < nkeys; j++, total++) {
            uint64_t number = uni_dist(gen);
            fout << number << "\n";
        }
        fout.close();
    }

    return 0;
}
