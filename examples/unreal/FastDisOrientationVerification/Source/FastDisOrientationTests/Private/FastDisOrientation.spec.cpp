#include "Misc/AutomationTest.h"

#include "FastDisWorldSubsystem.h"

#include "Dom/JsonObject.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
FVector ReadVector(const TSharedPtr<FJsonObject>& Object, const FString& Name)
{
    const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
    if (!Object->TryGetArrayField(Name, Values) || Values == nullptr || Values->Num() != 3)
    {
        return FVector::ZeroVector;
    }
    return FVector(
        (*Values)[0]->AsNumber(),
        (*Values)[1]->AsNumber(),
        (*Values)[2]->AsNumber());
}

FVector ReadExpectedDirection(const TSharedPtr<FJsonObject>& Object, const FString& Name)
{
    return ReadVector(Object, Name).GetSafeNormal();
}

double AngleBetweenDirectionsDegrees(const FVector& Actual, const FVector& Expected)
{
    const double Dot = FMath::Clamp(FVector::DotProduct(Actual.GetSafeNormal(), Expected.GetSafeNormal()), -1.0, 1.0);
    return FMath::RadiansToDegrees(FMath::Acos(Dot));
}

bool LoadFixtureRoot(TSharedPtr<FJsonObject>& OutRoot, FString& OutError)
{
    const FString StagedFixture = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(FPaths::ProjectDir(), TEXT("Tests/orientation_engine_cases.json")));
    const FString ProjectFixture = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(FPaths::ProjectDir(), TEXT("../../tests/data/orientation_engine_cases.json")));
    const FString RepoFixture = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(FPaths::ProjectDir(), TEXT("../../../../tests/data/orientation_engine_cases.json")));

    FString Json;
    FString FixturePath = RepoFixture;
    if (FPaths::FileExists(StagedFixture))
    {
        FixturePath = StagedFixture;
    }
    else if (FPaths::FileExists(ProjectFixture))
    {
        FixturePath = ProjectFixture;
    }
    if (!FFileHelper::LoadFileToString(Json, *FixturePath))
    {
        OutError = FString::Printf(TEXT("Could not load fixture file: %s"), *FixturePath);
        return false;
    }

    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Json);
    if (!FJsonSerializer::Deserialize(Reader, OutRoot) || !OutRoot.IsValid())
    {
        OutError = TEXT("Could not parse orientation fixture JSON");
        return false;
    }
    return true;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FFastDisUnrealOrientationBasisSpec,
    "FastDis.Orientation.UnrealBasisFixtures",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FFastDisUnrealOrientationBasisSpec::RunTest(const FString& Parameters)
{
    TSharedPtr<FJsonObject> Root;
    FString Error;
    if (!LoadFixtureRoot(Root, Error))
    {
        AddError(Error);
        return false;
    }

    const TSharedPtr<FJsonObject> Tolerances = Root->GetObjectField(TEXT("tolerances"));
    const double MaxAngleDegrees = Tolerances->GetNumberField(TEXT("engine_axis_angular_error_deg"));

    const TArray<TSharedPtr<FJsonValue>>* Cases = nullptr;
    if (!Root->TryGetArrayField(TEXT("cases"), Cases) || Cases == nullptr || Cases->Num() == 0)
    {
        AddError(TEXT("Fixture has no cases"));
        return false;
    }

    for (const TSharedPtr<FJsonValue>& CaseValue : *Cases)
    {
        const TSharedPtr<FJsonObject> Case = CaseValue->AsObject();
        const FString CaseName = Case->GetStringField(TEXT("name"));
        const TSharedPtr<FJsonObject> Expected = Case->GetObjectField(TEXT("expected"));
        const TSharedPtr<FJsonObject> Attitude = Case->GetObjectField(TEXT("local_ned_attitude_deg"));

        FFastDisRuntimeSettings Settings;
        Settings.Georeference.LatitudeDegrees = Case->GetNumberField(TEXT("lat_deg"));
        Settings.Georeference.LongitudeDegrees = Case->GetNumberField(TEXT("lon_deg"));
        Settings.Georeference.HeightMeters = Case->GetNumberField(TEXT("height_m"));
        Settings.Georeference.bApplyOrientation = true;
        Settings.TransformMode = EFastDisTransformMode::SnapPositionAndExperimentalRotation;

        bool bApplyRotation = false;
        const FTransform Transform = UFastDisWorldSubsystem::BuildDebugTransformForLocalAttitude(
            Settings,
            Attitude->GetNumberField(TEXT("heading")),
            Attitude->GetNumberField(TEXT("pitch")),
            Attitude->GetNumberField(TEXT("roll")),
            bApplyRotation);

        TestTrue(*FString::Printf(TEXT("%s apply rotation"), *CaseName), bApplyRotation);

        const FVector ExpectedForward = ReadExpectedDirection(Expected, TEXT("unreal_forward"));
        const FVector ExpectedRight = ReadExpectedDirection(Expected, TEXT("unreal_right"));
        const FVector ExpectedUp = ReadExpectedDirection(Expected, TEXT("unreal_up"));

        const FVector ActualForward = Transform.GetRotation().GetAxisX();
        const FVector ActualRight = Transform.GetRotation().GetAxisY();
        const FVector ActualUp = Transform.GetRotation().GetAxisZ();

        TestTrue(*FString::Printf(TEXT("%s forward"), *CaseName),
            AngleBetweenDirectionsDegrees(ActualForward, ExpectedForward) <= MaxAngleDegrees);
        TestTrue(*FString::Printf(TEXT("%s right"), *CaseName),
            AngleBetweenDirectionsDegrees(ActualRight, ExpectedRight) <= MaxAngleDegrees);
        TestTrue(*FString::Printf(TEXT("%s up"), *CaseName),
            AngleBetweenDirectionsDegrees(ActualUp, ExpectedUp) <= MaxAngleDegrees);
    }

    return true;
}

#endif
