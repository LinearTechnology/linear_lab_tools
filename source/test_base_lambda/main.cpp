#include <iostream>
#include <cstdint>
using std::cout;

class Base {
public:
    virtual void F1(uint32_t* i) = 0;
    void F1(uint16_t* i) {
        cout << "Called Base::F1(" << *i << ");\n";
    }
};

class Derived : public Base {
public:
    using Base::F1;
    void F1(uint32_t* i) override {
        cout << "Called Derived::F1(" << *i << ");\n";
    }
};

template <typename Func>
void DoLambda(Func f) {
    f();
}

int main() {
    Derived d;
    Base& b = d;
    uint16_t one = 1;
    uint32_t two = 2;
    uint16_t three = 3;
    uint32_t four = 4;
    d.F1(&one);
    d.F1(&two);
    DoLambda([&]{ d.F1(&three); });
    DoLambda([&]{ d.F1(&four); });
    return 0;
}