add_library(mqssd_util mqssd_util.cc)
add_executable(mqssd mqssd.cc)
target_include_directories (mqssd PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(mqssd LINK_PUBLIC mqssd_util rocksdb -lstdc++fs)
