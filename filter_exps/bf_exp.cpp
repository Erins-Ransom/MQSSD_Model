#include <random>

#include "bf.hpp"

std::random_device rd;
std::mt19937_64 gen(rd());
std::uniform_int_distribution<uint64_t> uni_dist(0, UINT64_MAX);

int main(int argc, char **argv) {
    size_t nkeys = 1000;
    size_t nbits = 10000;
    BloomFilter* bf = new BloomFilter(nbits, nkeys);
    // for (size_t i = 0; i < nkeys; i++) {
    //     bf->insert(uni_dist(gen));
    // }
    delete bf;
}