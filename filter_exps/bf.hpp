#pragma once
#ifndef BF_HPP
#define BF_HPP

#include <sys/mman.h>
#include <inttypes.h>
#include <fcntl.h>
#include <unistd.h>
#include <vector>
#include <memory>
#include <cstring>
#include <cmath>
#include <random>
#include <stdexcept>
#include <filesystem>
#include <fstream>

#include "MurmurHash3.hpp"

inline uint32_t mod8(uint32_t a) {
    return a & 7U;
}

inline uint32_t div8(uint32_t a) {
    return a >> 3;
}

class BloomFilter {
    private:
        uint8_t* data_;
        uint64_t nmod_;
        std::vector<uint32_t> seeds_;
        size_t mdlen_;
        size_t len_;
        int fd_;

    public:
        BloomFilter(uint64_t nbits, uint64_t nkeys) : 
            // Filter uses 32-bit MurmurHash function so the number of filter bits cannot be more than UINT32_MAX
            nmod_(std::min(static_cast<uint64_t>(UINT32_MAX), ((nbits + 7) / 8 * 8))) {  
            
            if (nbits == 0 || nkeys == 0) {
                throw std::invalid_argument("nbits and nkeys must be positive");
            }

            // Calculate the optimal number of hash functions
            uint32_t nhf = static_cast<uint32_t>(round(M_LN2 * nmod_ / nkeys));
            nhf = (nhf == 0 ? 1 : nhf);
            
            // Generate the hash seeds 
            seeds_.resize(nhf);
            std::mt19937 gen(1337);
            for (uint32_t i = 0; i < nhf; ++i) {
                seeds_[i] = gen();
            }

            // Write metadata to file
            std::ofstream fout;
            fout.open("bf.bin", std::ios::binary | std::ios::out);

            uint32_t seeds_sz = seeds_.size();
            fout.write(reinterpret_cast<const char*>(&seeds_sz), sizeof(seeds_sz));
            fout.write(reinterpret_cast<const char*>(seeds_.data()), sizeof(uint32_t) * seeds_.size());
            fout.write(reinterpret_cast<const char*>(&nmod_), sizeof(nmod_));

            // Get length of metadata 
            mdlen_ = fout.tellp();

            // Write empty filter bits to disk
            char zero[div8(nmod_)] = { 0 };
            fout.write(zero, sizeof(zero));

            // Get length of file
            len_ = fout.tellp();
            printf("%lu\n", len_);

            // Close file stream
            fout.close();

            // Get file descriptor
            fd_ = open("bf.bin", O_RDWR);
            if (fd_ == -1) {
                perror("open() failed");
                exit(EXIT_FAILURE);
            }
            
            // Memory map file
            data_ = static_cast<uint8_t*>(
                mmap(NULL, 
                     len_, 
                     PROT_READ | PROT_WRITE, 
                     MAP_SHARED_VALIDATE | MAP_SYNC, 
                     fd_, 
                     0)
            );

            if (data_ == MAP_FAILED) {
                perror("mmap() failed");
                exit(EXIT_FAILURE);
            }
        }

        ~BloomFilter() {
            // Unmap file
            munmap(data_, len_);

            // Close file descriptor
            int r = close(fd_);
            if (r == -1) {
                perror("close() failed");
                exit(EXIT_FAILURE); 
            }
        }

        bool get(uint64_t i) const {
            return (data_[div8(i) + mdlen_] >> (7 - mod8(i))) & 1;
        }

        void set(uint64_t i, bool v) {
            if (get(i) != v) {
                data_[div8(i) + mdlen_] ^= (1 << (7 - mod8(i)));
            }
        }
        
        uint64_t hash(const uint64_t k, const uint32_t& seed) {
            uint32_t h;
            MurmurHash3_x86_32(&k, 8, seed, &h);
            return static_cast<uint64_t>(h) % nmod_;
        }

        bool query(const uint64_t key) {
            bool out = true;
            for (size_t i = 0; i < seeds_.size() && out; ++i) {
                out &= get(hash(key, seeds_[i]));
            }
            return out;
        }

        void insert(const uint64_t key) {
            for (uint32_t i = 0; i < seeds_.size(); ++i) {
                set(hash(key, seeds_[i]), 1);
            }
        }
};

#endif