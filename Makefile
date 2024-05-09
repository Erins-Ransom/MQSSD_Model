# run make ASAN=1 all etc. to compile with address sanitizers
ASAN_SUFFIX := 
ifeq ($(ASAN),1)
	ASAN_SUFFIX := -fsanitize=address
endif

all: workload_gen.cc
	g++ -O3 -o workload_gen workload_gen.cc -Wall -Wextra --std=c++17 $(ASAN_SUFFIX)
clean:
	rm -f workload_gen