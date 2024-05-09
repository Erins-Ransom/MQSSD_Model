#include <cassert>
#include <vector>
#include <sstream>
#include <fstream>
#include <iterator>
#include <random>
#include <filesystem>

int main(int argc, char *argv[]) {
    assert(argc == 3);

    const std::string DATA_DIR = argv[1];
    unsigned long long nkeys = strtoull(argv[2], NULL, 0);

    assert(std::filesystem::exists(DATA_DIR));

    std::vector<uint64_t> keys;
    keys.reserve(nkeys);

    std::random_device rd;  // Will be used to obtain a seed for the random number engine
    std::mt19937_64 gen(rd()); // Standard mersenne_twister_engine seeded with rd()
    std::uniform_int_distribution<uint64_t> uni_dist(0, UINT64_MAX);

    while (keys.size() < nkeys) {
        uint64_t number = uni_dist(gen);
        keys.push_back(number);
    }

    std::stringstream ss;
    ss << nkeys << ".txt";
    std::ofstream output_file(ss.str());
    std::ostream_iterator<uint64_t> output_iterator(output_file, "\n");

    std::copy(keys.begin(), keys.end(), output_iterator);
    output_file.close();

    return 0;
}
