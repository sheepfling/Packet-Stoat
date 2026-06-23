#pragma once

#include "Components/ActorComponent.h"
#include "FastDisTypes.h"
#include "FastDisGeoreferenceAdapterComponent.generated.h"

UCLASS(ClassGroup = (FastDIS), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class FASTDISUNREAL_API UFastDisGeoreferenceAdapterComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UFastDisGeoreferenceAdapterComponent();

    virtual void BeginPlay() override;

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Georeference")
    bool ApplyManualGeoreference();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Georeference")
    bool ApplyFromSourceObject();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Georeference")
    bool ReadSourceGeoreference(FFastDisGeoreference& OutGeoreference) const;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Georeference")
    bool bApplyOnBeginPlay = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Georeference")
    FFastDisGeoreference ManualGeoreference;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Georeference")
    TObjectPtr<UObject> GeoreferenceSource = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Georeference")
    FName LatitudePropertyName = TEXT("LatitudeDegrees");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Georeference")
    FName LongitudePropertyName = TEXT("LongitudeDegrees");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Georeference")
    FName HeightPropertyName = TEXT("HeightMeters");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Georeference")
    FName ApplyOrientationPropertyName = TEXT("bApplyOrientation");

private:
    bool ApplyGeoreference(const FFastDisGeoreference& Georeference);
    static bool ReadNumericProperty(const UObject* Source, FName PropertyName, double& OutValue);
    static bool ReadBoolProperty(const UObject* Source, FName PropertyName, bool& OutValue);
};
