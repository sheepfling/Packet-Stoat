#include "Interfaces/IPluginManager.h"
#include "HAL/PlatformProcess.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"

namespace
{
#if PLATFORM_WINDOWS
void* GFastDisDllHandle = nullptr;
#endif
}

class FFastDisUnrealModule final : public IModuleInterface
{
public:
    virtual void StartupModule() override
    {
#if PLATFORM_WINDOWS
        const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("FastDis"));
        if (!Plugin.IsValid())
        {
            UE_LOG(LogTemp, Warning, TEXT("FastDisUnreal could not locate its plugin base directory"));
            return;
        }

        const FString BaseDir = Plugin->GetBaseDir();
        const FString PrimaryDllPath = FPaths::Combine(BaseDir, TEXT("Binaries"), TEXT("Win64"), TEXT("fastdis.dll"));
        GFastDisDllHandle = FPlatformProcess::GetDllHandle(*PrimaryDllPath);
        if (!GFastDisDllHandle)
        {
            const FString FallbackDllPath = FPaths::Combine(
                BaseDir, TEXT("Binaries"), TEXT("ThirdParty"), TEXT("fastdis"), TEXT("Win64"), TEXT("fastdis.dll"));
            GFastDisDllHandle = FPlatformProcess::GetDllHandle(*FallbackDllPath);
        }

        if (!GFastDisDllHandle)
        {
            UE_LOG(LogTemp,
                   Warning,
                   TEXT("FastDisUnreal could not preload fastdis.dll from %s"),
                   *BaseDir);
        }
#endif
    }

    virtual void ShutdownModule() override
    {
#if PLATFORM_WINDOWS
        if (GFastDisDllHandle)
        {
            FPlatformProcess::FreeDllHandle(GFastDisDllHandle);
            GFastDisDllHandle = nullptr;
        }
#endif
    }
};

IMPLEMENT_MODULE(FFastDisUnrealModule, FastDisUnreal)
