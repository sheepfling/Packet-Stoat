#include "Modules/ModuleManager.h"

class FFastDisUnrealModule final : public IModuleInterface
{
public:
    virtual void StartupModule() override {}
    virtual void ShutdownModule() override {}
};

IMPLEMENT_MODULE(FFastDisUnrealModule, FastDisUnreal)
