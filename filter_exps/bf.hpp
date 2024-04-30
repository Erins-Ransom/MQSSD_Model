#pragma once
#ifndef BF_HPP
#define BF_HPP

#include <vector>
#include <memory>
#include <cassert>
#include <inttypes.h>
#include <cstring>
#include <cmath>
#include <random>
#include <map>

#include "MurmurHash3.hpp"

class BloomFilter {
    private:
        uint8_t* data_;
        std::vector<uint32_t> seeds_;
        uint64_t nmod_;

    public:
        BloomFilter(uint64_t nbits, const std::vector<uint64_t>& keys) : 
            nmod_(std::min(static_cast<uint64_t>(UINT32_MAX), (nbits+7)/8*8)) {  
            // Filter uses 32-bit MurmurHash function so the number of filter bits cannot be more than UINT32_MAX.

            assert(nbits > 0);

            // Create zeroed out bit array - parentheses value initializes array to 0
            data_ = new uint8_t[nmod_ >> 3]();
            assert(data_);

            uint32_t nhf = static_cast<uint32_t>(round(M_LN2 * nmod_ / keys.size()));
            nhf = (nhf == 0 ? 1 : nhf);
            
            seeds_.resize(nhf);
            std::mt19937 gen(1337);
            for (uint32_t i = 0; i < nhf; ++i) {
                seeds_[i] = gen();
            }

            for (auto const & k : keys) {
                for (uint32_t i = 0; i < nhf; ++i) {
                    set(hash(k, seeds_[i]), 1);
                }
            }
        }

        ~BloomFilter() {
            delete[] data_;
        }

        bool Query(const uint64_t key) {
            bool out = true;
            for (size_t i = 0; i < seeds_.size() && out; ++i) {
                out &= get(hash(key, seeds_[i]));
            }
            return out;
        }

        bool get(uint64_t i) const {
            return (data_[i >> 3] >> (7 - (i & __UINT64_C(7)))) & 1;
        }

        void set(uint64_t i, bool v) {
            if (get(i) != v) {
                data_[i >> 3] ^= (1 << (7 - (i & __UINT64_C(7))));
            }
        }
        
        uint64_t hash(const uint64_t k, const uint32_t& seed) {
            uint32_t h;
            MurmurHash3_x86_32(&k, 8, seed, &h);
            return static_cast<uint64_t>(h) % nmod_;
        }
};

#endif