using UnrealBuildTool;
using System.IO;

public class FastDisUnreal : ModuleRules
{
    public FastDisUnreal(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        CppStandard = CppStandardVersion.Cpp20;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "Json",
            "JsonUtilities",
            "Networking",
            "RenderCore",
            "Sockets",
            "UMG"
        });

        if (Target.bBuildEditor)
        {
            PrivateDependencyModuleNames.Add("UnrealEd");
        }

        string ThirdPartyPath = Path.GetFullPath(Path.Combine(ModuleDirectory, "../../ThirdParty/fastdis"));
        PublicIncludePaths.Add(Path.Combine(ThirdPartyPath, "include"));

        if (Target.Platform == UnrealTargetPlatform.Win64)
        {
            string LibPath = Path.Combine(ThirdPartyPath, "lib", "Win64");
            string BinPath = Path.Combine(ThirdPartyPath, "bin", "Win64");
            PublicAdditionalLibraries.Add(Path.Combine(LibPath, "fastdis.lib"));
            PublicDelayLoadDLLs.Add("fastdis.dll");
            RuntimeDependencies.Add("$(PluginDir)/Binaries/ThirdParty/fastdis/Win64/fastdis.dll", Path.Combine(BinPath, "fastdis.dll"));
        }
        else if (Target.Platform == UnrealTargetPlatform.Linux)
        {
            string LibPath = Path.Combine(ThirdPartyPath, "lib", "Linux");
            PublicAdditionalLibraries.Add(Path.Combine(LibPath, "libfastdis.so"));
            foreach (string RuntimeLib in Directory.GetFiles(LibPath, "libfastdis.so*"))
            {
                RuntimeDependencies.Add("$(PluginDir)/Binaries/ThirdParty/fastdis/Linux/" + Path.GetFileName(RuntimeLib), RuntimeLib);
            }
        }
        else if (Target.Platform == UnrealTargetPlatform.Mac)
        {
            string LibPath = Path.Combine(ThirdPartyPath, "lib", "Mac");
            PublicAdditionalLibraries.Add(Path.Combine(LibPath, "libfastdis.dylib"));
            foreach (string RuntimeLib in Directory.GetFiles(LibPath, "libfastdis*.dylib"))
            {
                RuntimeDependencies.Add("$(PluginDir)/Binaries/ThirdParty/fastdis/Mac/" + Path.GetFileName(RuntimeLib), RuntimeLib);
            }
        }
    }
}
