CC=g++
CFLAGS=-std=c++14 -I. -I../ltc_controller_comm/
LFLAGS=-std=c++14 -L../ltc_controller_comm -l_ltc_controller_comm
DEPS=../ltc_controller_comm/ltc_controller_comm.h
OBJ=main.o
TARGET=test_llt

%.o: %.cpp $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS) $(CEXTRA)

$(TARGET): $(OBJ)
	$(CC) -o $@ $^ $(LFLAGS) $(LEXTRA)

.PHONY: clean
clean:
	rm -f *.o
