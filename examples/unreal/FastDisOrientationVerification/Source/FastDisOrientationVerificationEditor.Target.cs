using UnrealBuildTool;
using System.Collections.Generic;

public class FastDisOrientationVerificationEditorTarget : TargetRules
{
    public FastDisOrientationVerificationEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V6;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_7;
        ExtraModuleNames.AddRange(new List<string>
        {
            "FastDisOrientationVerification",
            "FastDisOrientationTests"
        });
    }
}
