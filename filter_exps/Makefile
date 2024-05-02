# run make ASAN=1 bf_exp to compile with address sanitizers
ASAN_SUFFIX := 
ifeq ($(ASAN),1)
	ASAN_SUFFIX := -fsanitize=address
endif

bf_exp: bf_exp.cpp
	g++ -Ofast -march=native *.cpp -o bf_exp --std=c++17 -Wall -Wextra -g $(ASAN_SUFFIX)

clean:
	rm -f bf_exp