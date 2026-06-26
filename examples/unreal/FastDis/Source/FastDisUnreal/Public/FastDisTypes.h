#pragma once

#include "CoreMinimal.h"
#include "FastDisTypes.generated.h"

class AActor;

UENUM(BlueprintType)
enum class EFastDisPduSurface : uint8
{
    Unknown UMETA(DisplayName = "Unknown"),
    EntityState UMETA(DisplayName = "Entity State"),
    EntityStateUpdate UMETA(DisplayName = "Entity State Update"),
    RemoveEntity UMETA(DisplayName = "Remove Entity"),
    Fire UMETA(DisplayName = "Fire"),
    Detonation UMETA(DisplayName = "Detonation"),
    StartResume UMETA(DisplayName = "Start/Resume"),
    StopFreeze UMETA(DisplayName = "Stop/Freeze"),
    ElectromagneticEmission UMETA(DisplayName = "Electromagnetic Emission"),
    Signal UMETA(DisplayName = "Signal"),
    Designator UMETA(DisplayName = "Designator"),
};

UENUM(BlueprintType)
enum class EFastDisRemoveEntityPolicy : uint8
{
    Destroy UMETA(DisplayName = "Destroy"),
    Hide UMETA(DisplayName = "Hide"),
    MarkStale UMETA(DisplayName = "Mark Stale"),
    Ignore UMETA(DisplayName = "Ignore"),
};

USTRUCT(BlueprintType)
struct FFastDisSendSocketInfo
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager|Structs")
    FString IpAddress = TEXT("127.0.0.1");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager|Structs", meta = (ClampMin = "1", ClampMax = "65535"))
    int32 Port = 3001;
};

USTRUCT(BlueprintType)
struct FFastDisReceiveSocketInfo
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager|Structs")
    FString IpAddress = TEXT("0.0.0.0");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager|Structs", meta = (ClampMin = "1", ClampMax = "65535"))
    int32 Port = 3001;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager|Structs", meta = (ClampMin = "512"))
    int32 ReceiveBufferBytes = 1048576;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager|Structs", meta = (ClampMin = "1"))
    int32 MaxPacketsPerTick = 256;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager|Structs")
    bool bAutoStart = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Manager|Structs")
    bool bApplySnapshotsImmediately = true;
};

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

USTRUCT(BlueprintType)
struct FFastDisEntityType
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    int32 Kind = -1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    int32 Domain = -1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    int32 Country = -1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    int32 Category = -1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    int32 Subcategory = -1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    int32 Specific = -1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    int32 Extra = -1;

    bool IsWildcard() const
    {
        return Kind < 0 || Domain < 0 || Country < 0 || Category < 0 || Subcategory < 0 || Specific < 0 || Extra < 0;
    }

    bool Matches(const FFastDisEntityType& Other) const
    {
        return (Kind < 0 || Kind == Other.Kind) &&
               (Domain < 0 || Domain == Other.Domain) &&
               (Country < 0 || Country == Other.Country) &&
               (Category < 0 || Category == Other.Category) &&
               (Subcategory < 0 || Subcategory == Other.Subcategory) &&
               (Specific < 0 || Specific == Other.Specific) &&
               (Extra < 0 || Extra == Other.Extra);
    }

    int32 Specificity() const
    {
        int32 Score = 0;
        Score += Kind >= 0 ? 1 : 0;
        Score += Domain >= 0 ? 1 : 0;
        Score += Country >= 0 ? 1 : 0;
        Score += Category >= 0 ? 1 : 0;
        Score += Subcategory >= 0 ? 1 : 0;
        Score += Specific >= 0 ? 1 : 0;
        Score += Extra >= 0 ? 1 : 0;
        return Score;
    }
};

USTRUCT(BlueprintType)
struct FFastDisPduHeader
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 Version = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 ExerciseId = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 PduType = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 ProtocolFamily = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 DeclaredLength = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 PacketSize = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    EFastDisPduSurface Surface = EFastDisPduSurface::Unknown;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FName PduName = NAME_None;
};

USTRUCT(BlueprintType)
struct FFastDisPduEvent
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FFastDisPduHeader Header;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FString SourceEndpoint;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    TArray<uint8> RawBytes;
};

USTRUCT(BlueprintType)
struct FFastDisRemoveEntityEvent
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FFastDisPduEvent BaseEvent;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId OriginatingEntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId ReceivingEntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 RequestId = 0;
};

USTRUCT(BlueprintType)
struct FFastDisEntityStateUpdateEvent
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FFastDisPduEvent BaseEvent;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId EntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FVector WorldLocationMeters = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FVector LinearVelocityMetersPerSecond = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FRotator DisOrientationRadians = FRotator::ZeroRotator;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    int32 Appearance = 0;
};

USTRUCT(BlueprintType)
struct FFastDisFireEvent
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FFastDisPduEvent BaseEvent;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId FiringEntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId TargetEntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId MunitionEntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 EventNumber = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 FireMissionIndex = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FVector WorldLocationMeters = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FVector VelocityMetersPerSecond = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    float RangeMeters = 0.0f;
};

USTRUCT(BlueprintType)
struct FFastDisDetonationEvent
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FFastDisPduEvent BaseEvent;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId FiringEntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId TargetEntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId MunitionEntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 EventNumber = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FVector WorldLocationMeters = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FVector VelocityMetersPerSecond = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 DetonationResult = 0;
};

USTRUCT(BlueprintType)
struct FFastDisStartResumeEvent
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FFastDisPduEvent BaseEvent;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId OriginatingEntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId ReceivingEntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int64 RealWorldTime = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int64 SimulationTime = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 RequestId = 0;
};

USTRUCT(BlueprintType)
struct FFastDisStopFreezeEvent
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FFastDisPduEvent BaseEvent;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId OriginatingEntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId ReceivingEntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int64 RealWorldTime = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 Reason = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 FrozenBehavior = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 RequestId = 0;
};

USTRUCT(BlueprintType)
struct FFastDisEmissionEvent
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FFastDisPduEvent BaseEvent;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId EmittingEntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 EventNumber = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 StateUpdateIndicator = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 SystemCount = 0;
};

USTRUCT(BlueprintType)
struct FFastDisSignalEvent
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FFastDisPduEvent BaseEvent;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId EntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 RadioId = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 EncodingScheme = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 TdlType = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 SampleRate = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 DataLengthBits = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 SampleCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    TArray<uint8> SignalData;
};

USTRUCT(BlueprintType)
struct FFastDisDesignatorEvent
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FFastDisPduEvent BaseEvent;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId DesignatingEntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId DesignatedEntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 CodeName = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    int32 DesignatorCode = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    float Power = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    float Wavelength = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FVector SpotLocationMeters = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|PDU")
    FVector SpotLocationRelativeMeters = FVector::ZeroVector;
};

USTRUCT(BlueprintType)
struct FFastDisEntityTransformEvent
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityId EntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FFastDisEntityType EntityType;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    FTransform Transform;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Entity")
    bool bAppliedRotation = false;
};

USTRUCT(BlueprintType)
struct FFastDisUdpStats
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|UDP")
    int64 PacketsReceived = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|UDP")
    int64 PacketsSent = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|UDP")
    int64 BytesReceived = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|UDP")
    int64 BytesSent = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|UDP")
    int64 MalformedPackets = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|UDP")
    int64 DroppedPackets = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|UDP")
    FString LastEndpoint;
};

USTRUCT(BlueprintType)
struct FFastDisRuntimeMonitorSnapshot
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    bool bReceiverRunning = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    int32 KnownEntities = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    int64 PacketsReceived = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    int64 PacketsSent = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    int64 BytesReceived = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    int64 BytesSent = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    int64 MalformedPackets = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    int64 DroppedPackets = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    int64 PduEvents = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    int64 PduMalformedEvents = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    int32 LastPduType = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    FName LastPduName = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    FString LastEndpoint;
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

UENUM(BlueprintType)
enum class EFastDisTransformMode : uint8
{
    PositionOnly UMETA(DisplayName = "Position Only"),
    SnapPosition UMETA(DisplayName = "Snap Position"),
    InterpolatePosition UMETA(DisplayName = "Interpolate Position"),
    SnapPositionAndExperimentalRotation UMETA(DisplayName = "Position + Experimental Rotation"),
};

UENUM(BlueprintType)
enum class EFastDisOrientationMode : uint8
{
    Disabled UMETA(DisplayName = "Disabled"),
    ExperimentalLocalYawPitchRoll UMETA(DisplayName = "Experimental Local Heading/Pitch/Roll"),
    ValidatedDisBodyFrame UMETA(DisplayName = "Validated DIS Body Frame"),
};

USTRUCT(BlueprintType)
struct FFastDisRuntimeSettings
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS")
    FFastDisGeoreference Georeference;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Frame")
    EFastDisOrientationMode OrientationMode = EFastDisOrientationMode::ExperimentalLocalYawPitchRoll;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS")
    EFastDisTransformMode TransformMode = EFastDisTransformMode::PositionOnly;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS", meta = (ClampMin = "1.0"))
    double MetersToUnrealScale = 100.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS", meta = (ClampMin = "2", UIMin = "2"))
    int32 SnapshotSlots = 3;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS", meta = (ClampMin = "0", UIMin = "0"))
    int32 StaleAfterTicks = 120;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS", meta = (ClampMin = "0.01", UIMin = "0.01"))
    float InterpolationSpeed = 8.0f;
};

USTRUCT(BlueprintType)
struct FFastDisActorBinding
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS")
    FFastDisEntityId EntityId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS")
    TObjectPtr<AActor> Actor = nullptr;
};
