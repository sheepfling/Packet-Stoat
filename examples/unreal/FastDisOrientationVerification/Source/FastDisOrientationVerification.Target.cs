using UnrealBuildTool;
using System.Collections.Generic;

public class FastDisOrientationVerificationTarget : TargetRules
{
    public FastDisOrientationVerificationTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V6;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_7;
        ExtraModuleNames.AddRange(new List<string>
        {
            "FastDisOrientationVerification"
        });
    }
}
