#include <iostream>
#include <fstream>
#include <string>
#include <stdexcept>
#include <cstdint>
using std::ifstream;
using std::ofstream;
using std::wstring;
using std::runtime_error;
const int FPGA_PAGE_SIZE = 256;
const int NUM_FPGA_PAGES = 512;
class PageBuffer {
public:
    static const int FPGA_SIZE = NUM_FPGA_PAGES * FPGA_PAGE_SIZE;
    PageBuffer(wstring path) : file(path, std::ios::binary | std::ios::beg) { }
    bool GetPage(char data[FPGA_PAGE_SIZE]) {
        while (file.get(byte)) {
            if (total_bytes == FPGA_SIZE) {
                throw runtime_error("Expanded file too large (bad or corrupted squeeze file?)");
            }
            buffer[page_bytes] = byte;
            ++page_bytes;
            ++total_bytes;
            if (byte == 0) {
                if (!file.get(byte)) {
                    throw runtime_error("Error reading squeeze file (bad or corrupted?)");
                }
                uint8_t count = byte - 1;
                while (count != 0) {
                    if (total_bytes == FPGA_SIZE) {
                        throw runtime_error(
                            "Expanded file too large (bad or corrupted squeeze file?)");
                    }
                    buffer[page_bytes] = 0;
                    --count;
                    ++page_bytes;
                    ++total_bytes;
                }
            }
            if (page_bytes >= FPGA_PAGE_SIZE) {
                memcpy(data, buffer, FPGA_PAGE_SIZE);
                for (int i = FPGA_PAGE_SIZE; i < page_bytes; ++i) {
                    buffer[i - FPGA_PAGE_SIZE] = buffer[i];
                }
                page_bytes -= FPGA_PAGE_SIZE;
                return true;
            }
        }
        if (total_bytes != FPGA_SIZE) {
            throw runtime_error("Expanded file too small (bad or corrupted squeeze file?)");
        }
        return false;
    }
private:
    ifstream file;
    int total_bytes = 0;
    int page_bytes = 0;
    char buffer[2 * FPGA_PAGE_SIZE];
    char byte;
};

int main() {
    wstring filename(L"C:/Users/jeremy_s.ENGINEERING/Desktop/LinearLabTools/fpga_loads/dlvdsr1.sqz");
    wstring output_filename(L"C:/Users/jeremy_s.ENGINEERING/Desktop/LinearLabTools/fpga_loads/dlvdsr1.bit");

    ofstream output(output_filename, std::ios::binary | std::ios::beg);
    if (!output) {
        throw runtime_error("Could not open file dlvdsr1.bit for writing.");
    }

    PageBuffer page_buffer(filename);
    char data[FPGA_PAGE_SIZE];
    while (page_buffer.GetPage(data)) {
        output.write(data, FPGA_PAGE_SIZE);
    }
    return 0;
}