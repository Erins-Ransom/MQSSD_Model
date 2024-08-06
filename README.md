```
cd rocksdb-8.6.7
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DWITH_LZ4=ON ..
make -j$(nproc) mqssd reader
```

`cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo -DWITH_LZ4=1 -DUSE_COROUTINES=1 -DROCKSDB_BUILD_SHARED=0 ..`

https://github.com/facebook/rocksdb/wiki/RocksDB-Contribution-Guide#folly-integration

- Checkout and build folly
-  `CC=gcc-10 CXX=g++-10 mkdir -p build && cd build && cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo -DUSE_COROUTINES=1 -DWITH_GFLAGS=1 -DROCKSDB_BUILD_SHARED=0 .. && make -j`
