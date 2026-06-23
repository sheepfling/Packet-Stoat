#pragma once

#include "Components/ActorComponent.h"
#include "FastDisTypes.h"
#include "FastDisSampleTrafficComponent.generated.h"

/**
 * Small runtime sample component for validating the FastDIS Unreal path.
 *
 * Attach it to an actor, press Inject Sample Packet from Blueprint/C++, and the
 * component will feed one synthetic Entity State PDU through UFastDisWorldSubsystem.
 */
UCLASS(ClassGroup = (FastDIS), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class FASTDISUNREAL_API UFastDisSampleTrafficComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UFastDisSampleTrafficComponent();

    virtual void BeginPlay() override;

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Sample")
    void RegisterOwnerWithFastDis();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Sample")
    void InjectSamplePacket(bool bApplyImmediately = true);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Sample")
    TArray<uint8> BuildSampleEntityStatePacket() const;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Sample")
    FFastDisEntityId EntityId = FFastDisEntityId(0x1111, 0x2222, 0x3333);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Sample")
    uint8 ExerciseId = 3;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Sample")
    uint8 ForceId = 2;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Sample")
    FFastDisGeoreference Georeference;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Sample")
    FVector LocalOffsetMeters = FVector(25.0, 10.0, 0.0);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Sample")
    bool bRegisterOnBeginPlay = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Sample")
    bool bInjectOnBeginPlay = true;
};
