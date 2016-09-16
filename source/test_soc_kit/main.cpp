#include <iostream>
#include "../ltc_controller_comm/soc_kit.hpp"

using namespace linear;

int main() {
    LccControllerInfo info;
    strcpy(info.description, "SocKit");
    strcpy(info.serial_number, "12345");
    info.type = LCC_TYPE_SOC_KIT;
    info.id = 0x0A36025B;

    SocKit sockit(info);

    sockit.WriteRegisterDummy(0x00000004, 0x0000000C);
    auto reg = sockit.ReadRegisterDummy(0x00000004);
    std::cout << "Reg = " << reg << "\n";

    sockit.Shutdown();

}