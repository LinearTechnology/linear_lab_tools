#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <utility>
#include <regex>
#include <stdexcept>
#include "gsl"

using std::string;
using std::ifstream;
using std::ofstream;
using std::vector;
using std::pair;
using std::make_pair;
using std::regex;
using std::smatch;
using std::regex_search;
using std::runtime_error;

using gsl::narrow;

void remove_includes(string& code) {
    const regex include_re("#include[ \\t]+[^\\n]+\\n");
    while (true) {
        smatch include_match;
        if (regex_search(code, include_match, include_re)) {
            auto start = include_match.position();
            auto size = include_match[0].length();
            code = code.replace(start, size, "");
        } else {
            return;
        }
    }
}

void replace_item(string& code, const string& item, const string& new_item) {
    while (true) {
        auto offset = code.find(item);
        if (offset == code.npos) { return; }
        code = code.replace(offset, item.size(), new_item);
    }
}

void replace_stdint(string& code) {
    replace_item(code, "bool ", "unsigned char ");
    replace_item(code, "uint8_t ", "unsigned char ");
    replace_item(code, "int8_t ", "char ");
    replace_item(code, "uint16_t ", "unsigned short ");
    replace_item(code, "int16_t ", "short ");
    replace_item(code, "uint32_t ", "unsigned int ");
    replace_item(code, "int32_t ", "int ");

    replace_item(code, "bool\t", "unsigned char\t");
    replace_item(code, "uint8_t\t", "unsigned char\t");
    replace_item(code, "int8_t\t", "char\t");
    replace_item(code, "uint16_t\t", "unsigned short\t");
    replace_item(code, "int16_t\t", "short\t");
    replace_item(code, "uint32_t\t", "unsigned int\t");
    replace_item(code, "int32_t\t", "int\t");

    replace_item(code, "bool*", "unsigned char*");
    replace_item(code, "uint8_t*", "unsigned char*");
    replace_item(code, "int8_t*", "char*");
    replace_item(code, "uint16_t*", "unsigned short*");
    replace_item(code, "int16_t*", "short*");
    replace_item(code, "uint32_t*", "unsigned int*");
    replace_item(code, "int32_t*", "int*");
}

void const_to_pound_define(string& code) {
    const std::regex const_re(
        "(const[ \\t]+)(unsigned[ \\t]+)?(char[ \\t]*\\*|char|short|int|long|float|double)[ \\t]+"
        "([0-9a-zA-Z_]+[ \\t]*)=[ \\t]*([^;]+);"
    );
    while (true) {
        smatch const_match;
        if (regex_search(code, const_match, const_re)) {
            auto replacement = string("#define ") + const_match[4].str() + " " + const_match[5].str();
            auto start = const_match.position();
            auto size = const_match[0].length();
            code = code.replace(start, size, replacement);
        } else {
            return;
        }
    }
}

vector<string> find_structs(const string& code) {
    const std::regex struct_re(
        "typedef[ \\t]+struct[ \\t]+[0-9a-zA-Z_]+[ \\t]*\\{[^\\}]+\\}[ \\t]*([0-9a-zA-Z_]+)[ \\t]*;"
    );

    vector<string> struct_names;
    auto begin = code.begin();
    auto end = code.end();
    while (true) {
        smatch struct_match;
        if (regex_search(begin, end, struct_match, struct_re)) {
            struct_names.push_back(struct_match[1].str());
            begin += (struct_match.position() + struct_match[0].length());
        } else {
            return struct_names;
        }
    }
}

void replace_structs(string& code, const vector<string>& vector_names) {
    for (auto& vector_name : vector_names) {
        std::regex func_re(string("(") + vector_name + "[ \\t]*\\*)");
        while (true) {
            smatch func_match;
            if (regex_search(code, func_match, func_re)) {
                auto start = func_match.position();
                auto size = func_match[1].length();
                code = code.replace(start, size, "unsigned char*");
            } else {
                return;
            }
        }
    }

}

string get_file_contents(const char *filename) {
    std::ifstream in(filename, std::ios::in | std::ios::binary);
    if (!in) {
        throw runtime_error(string("could not open file ") + filename);
    }
    std::string contents;
    in.seekg(0, std::ios::end);
    contents.resize(narrow<unsigned int>(in.tellg()));
    in.seekg(0, std::ios::beg);
    in.read(&contents[0], contents.size());
    return contents;
}

void write_file(const char* filename, const string& data) {
    ofstream out(filename, std::ios::out | std::ios::binary);
    if (!out) {
        throw runtime_error(string("could not open file ") + filename);
    }
    out.write(data.c_str(), data.size());
}

int main(int argc, char* argv[]) {
    auto code = get_file_contents(argv[1]);
    remove_includes(code);
    replace_stdint(code);
    const_to_pound_define(code);
    auto struct_names = find_structs(code);
    replace_structs(code, struct_names);
    if (code[code.length() - 1] != '\n') {
        code += "\n";
    }
    write_file(argv[2], code);
}



