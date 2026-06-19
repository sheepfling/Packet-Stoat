#pragma once

#include "CoreMinimal.h"
#include "FastDisTypes.generated.h"

USTRUCT(BlueprintType)
struct FFastDisEntityId
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS")
    int32 Site = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS")
    int32 Application = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS")
    int32 Entity = 0;

    FFastDisEntityId() = default;
    FFastDisEntityId(uint16 InSite, uint16 InApplication, uint16 InEntity)
        : Site(static_cast<int32>(InSite)), Application(static_cast<int32>(InApplication)), Entity(static_cast<int32>(InEntity)) {}

    bool operator==(const FFastDisEntityId& Other) const
    {
        return Site == Other.Site && Application == Other.Application && Entity == Other.Entity;
    }
};

FORCEINLINE uint32 GetTypeHash(const FFastDisEntityId& Id)
{
    uint32 Hash = ::GetTypeHash(Id.Site);
    Hash = HashCombine(Hash, ::GetTypeHash(Id.Application));
    Hash = HashCombine(Hash, ::GetTypeHash(Id.Entity));
    return Hash;
}

USTRUCT(BlueprintType)
struct FFastDisGeoreference
{
    GENERATED_BODY()

    // WGS-84 origin for the local tangent plane. DIS Entity State locations are
    // geocentric/ECEF meters, not Unreal world centimeters.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Frame")
    double LatitudeDegrees = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Frame")
    double LongitudeDegrees = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Frame")
    double HeightMeters = 0.0;

    // Keep this false until your exercise/profile orientation convention has
    // been validated. Position conversion is deterministic; orientation is often
    // profile/asset dependent.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Frame")
    bool bApplyOrientation = false;
};
