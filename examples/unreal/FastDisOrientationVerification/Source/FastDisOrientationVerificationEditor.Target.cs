using UnrealBuildTool;
using System.Collections.Generic;
using System;

public class FastDisOrientationVerificationEditorTarget : TargetRules
{
    public FastDisOrientationVerificationEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = ResolveBuildSettingsVersion();
        ExtraModuleNames.AddRange(new List<string>
        {
            "FastDisOrientationVerification",
            "FastDisOrientationTests"
        });
    }

    private static BuildSettingsVersion ResolveBuildSettingsVersion()
    {
        if (Enum.TryParse("V7", out BuildSettingsVersion v7))
        {
            return v7;
        }
        if (Enum.TryParse("V6", out BuildSettingsVersion v6))
        {
            return v6;
        }
        if (Enum.TryParse("V5", out BuildSettingsVersion v5))
        {
            return v5;
        }
        return BuildSettingsVersion.Latest;
    }
}
