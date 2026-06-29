#include "FastDisOrientationProbeActor.h"

#include "DrawDebugHelpers.h"

AFastDisOrientationProbeActor::AFastDisOrientationProbeActor()
{
    PrimaryActorTick.bCanEverTick = true;
}

double AFastDisOrientationProbeActor::AngleBetweenDirectionsDegrees(const FVector& Actual, const FVector& Expected)
{
    const FVector A = Actual.GetSafeNormal();
    const FVector B = Expected.GetSafeNormal();
    const double Dot = FMath::Clamp(FVector::DotProduct(A, B), -1.0, 1.0);
    return FMath::RadiansToDegrees(FMath::Acos(Dot));
}

FFastDisOrientationProbeResult AFastDisOrientationProbeActor::EvaluateBasis() const
{
    FFastDisOrientationProbeResult Result;
    Result.CaseName = CaseName;
    const FVector ActualForward = GetActorForwardVector().GetSafeNormal();
    const FVector ActualRight = GetActorRightVector().GetSafeNormal();
    const FVector ActualUp = GetActorUpVector().GetSafeNormal();
    const FVector ExpectedForward = ExpectedAxes.ExpectedForward.GetSafeNormal();
    const FVector ExpectedRight = ExpectedAxes.ExpectedRight.GetSafeNormal();
    const FVector ExpectedUp = ExpectedAxes.ExpectedUp.GetSafeNormal();

    Result.ForwardAngleDegrees = AngleBetweenDirectionsDegrees(ActualForward, ExpectedForward);
    Result.RightAngleDegrees = AngleBetweenDirectionsDegrees(ActualRight, ExpectedRight);
    Result.UpAngleDegrees = AngleBetweenDirectionsDegrees(ActualUp, ExpectedUp);
    Result.ForwardDot = FVector::DotProduct(ActualForward, ExpectedForward);
    Result.RightDot = FVector::DotProduct(ActualRight, ExpectedRight);
    Result.UpDot = FVector::DotProduct(ActualUp, ExpectedUp);
    Result.bPassed = Result.ForwardAngleDegrees <= MaxAxisAngleDegrees &&
        Result.RightAngleDegrees <= MaxAxisAngleDegrees &&
        Result.UpAngleDegrees <= MaxAxisAngleDegrees;
    return Result;
}

FString AFastDisOrientationProbeActor::FormatProbeStatusText() const
{
    const FFastDisOrientationProbeResult Result = EvaluateBasis();
    return FString::Printf(
        TEXT("%s %s\nforward angle=%.6f dot=%.6f\nright angle=%.6f dot=%.6f\nup angle=%.6f dot=%.6f\nthreshold=%.6f"),
        Result.bPassed ? TEXT("PASS") : TEXT("FAIL"),
        *Result.CaseName,
        Result.ForwardAngleDegrees,
        Result.ForwardDot,
        Result.RightAngleDegrees,
        Result.RightDot,
        Result.UpAngleDegrees,
        Result.UpDot,
        MaxAxisAngleDegrees);
}

void AFastDisOrientationProbeActor::DrawVerificationAxes(float DurationSeconds) const
{
    UWorld* World = GetWorld();
    if (World == nullptr)
    {
        return;
    }

    const FVector Origin = GetActorLocation();
    constexpr float AxisLength = 200.0f;

    DrawDebugDirectionalArrow(World, Origin, Origin + GetActorForwardVector() * AxisLength, 20.0f, FColor::Red, false, DurationSeconds, 0, 3.0f);
    DrawDebugDirectionalArrow(World, Origin, Origin + GetActorRightVector() * AxisLength, 20.0f, FColor::Green, false, DurationSeconds, 0, 3.0f);
    DrawDebugDirectionalArrow(World, Origin, Origin + GetActorUpVector() * AxisLength, 20.0f, FColor::Blue, false, DurationSeconds, 0, 3.0f);

    DrawDebugDirectionalArrow(World, Origin, Origin + ExpectedAxes.ExpectedForward.GetSafeNormal() * AxisLength * 0.8f, 20.0f, FColor::Red, false, DurationSeconds, 0, 1.0f);
    DrawDebugDirectionalArrow(World, Origin, Origin + ExpectedAxes.ExpectedRight.GetSafeNormal() * AxisLength * 0.8f, 20.0f, FColor::Green, false, DurationSeconds, 0, 1.0f);
    DrawDebugDirectionalArrow(World, Origin, Origin + ExpectedAxes.ExpectedUp.GetSafeNormal() * AxisLength * 0.8f, 20.0f, FColor::Blue, false, DurationSeconds, 0, 1.0f);

    if (bDrawStatusText)
    {
        const FFastDisOrientationProbeResult Result = EvaluateBasis();
        DrawDebugString(
            World,
            Origin + FVector(0.0f, 0.0f, StatusTextZOffset),
            FormatProbeStatusText(),
            nullptr,
            Result.bPassed ? FColor::Green : FColor::Red,
            DurationSeconds,
            true);
    }
}

void AFastDisOrientationProbeActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    DrawVerificationAxes(0.0f);
}
