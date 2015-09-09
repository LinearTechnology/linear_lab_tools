#include <iostream>
#include <memory>
using std::unique_ptr;
using std::make_unique;
using std::cout;
class Base {
public:
    void NonVirtual() { cout << "Called Base::NonVirtual\n"; }
    virtual void Virtual() { cout << "Called Base::Virtual\n"; }
    virtual ~Base() { }
};

class IRed: virtual public Base {
public:
    virtual void Red() = 0;
    virtual ~IRed() { }
};

class IBlue : virtual public Base {
public:
    virtual void Blue() = 0;
    virtual ~IBlue() { }
};

class Derived : public IRed, IBlue {
public:
    void Virtual() override { cout << "Called Derived::Virtual\n"; }
    void Red() override { cout << "Called Derived::Red\n";}
    void Blue() override { cout << "Called Derived::Blue\n"; }
};

class DRed : public IRed {
public:
    void Virtual() override { cout << "Called DRed::Virtual\n"; }
    void Red() override { cout << "Called DRed::Red\n"; }
};

int main() {
    auto d = make_unique<Derived>();
    auto r = make_unique<DRed>();

    Base* base1 = d.get();
    Base* base2 = r.get();

    base1->Virtual();
    auto dr = dynamic_cast<IRed*>(base1);
    dr->Red();
    dynamic_cast<IBlue*>(base1)->Blue();
    auto rr = dynamic_cast<IRed*>(base2);
    rr->Red();
    auto rb = dynamic_cast<IBlue*>(base2);
    rb->Blue();

    return 0;
}