CC=g++
CFLAGS=-std=c++14 -fpic -I. -I../../../boost_1_63_0 -I../../../gsl -I../../../ftdi
LFLAGS=-std=c++14 -shared -lstdc++fs -ldl
DEPS=ltc_controller_comm.h utilities.hpp ftdi.hpp ftdi_adc.hpp dc718.hpp dc890.hpp \
     high_speed.hpp i_close.hpp i_data_receive.hpp i_reset.hpp i_collect.hpp i_data_send.hpp  \
     i_spi.hpp i_data_endian.hpp i_fpga_load.hpp i_spi_send_only.hpp
OBJ=ltc_controller_comm.o utilties.o ftdi.o ftdi_adc.o high_speed.o dc890.o dllmain.o
TARGET=lib_ltc_controller_comm.so

%.o: %.cpp $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS) $(CEXTRA)

$(TARGET): $(OBJ)
	$(CC) -o $@ $^ $(LFLAGS) $(LEXTRA)

.PHONY: clean
clean:
	rm -f *.o
