using UnrealBuildTool;

public class FastDisOrientationTests : ModuleRules
{
    public FastDisOrientationTests(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new[]
        {
            "Core",
            "CoreUObject",
            "Engine"
        });

        PrivateDependencyModuleNames.AddRange(new[]
        {
            "Json",
            "JsonUtilities",
            "UnrealEd",
            "FunctionalTesting",
            "FastDisUnreal"
        });
    }
}
