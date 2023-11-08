```
cd rocksdb-8.6.7
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DWITH_LZ4=ON ..
make -j$(nproc) mqssd
```