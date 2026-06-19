#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "FastDisOrientationProbeActor.generated.h"

USTRUCT(BlueprintType)
struct FFastDisOrientationExpectedAxes
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS")
    FVector ExpectedForward = FVector::ForwardVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS")
    FVector ExpectedRight = FVector::RightVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS")
    FVector ExpectedUp = FVector::UpVector;
};

USTRUCT(BlueprintType)
struct FFastDisOrientationProbeResult
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS")
    FString CaseName;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS")
    double ForwardAngleDegrees = 0.0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS")
    double RightAngleDegrees = 0.0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS")
    double UpAngleDegrees = 0.0;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "FastDIS")
    bool bPassed = false;
};

UCLASS()
class AFastDisOrientationProbeActor : public AActor
{
    GENERATED_BODY()

public:
    AFastDisOrientationProbeActor();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS")
    FString CaseName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS")
    FFastDisOrientationExpectedAxes ExpectedAxes;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS")
    double MaxAxisAngleDegrees = 0.01;

    UFUNCTION(BlueprintCallable, Category = "FastDIS")
    FFastDisOrientationProbeResult EvaluateBasis() const;

    UFUNCTION(BlueprintCallable, Category = "FastDIS")
    void DrawVerificationAxes(float DurationSeconds = 0.0f) const;

    static double AngleBetweenDirectionsDegrees(const FVector& Actual, const FVector& Expected);

protected:
    virtual void Tick(float DeltaSeconds) override;
};
