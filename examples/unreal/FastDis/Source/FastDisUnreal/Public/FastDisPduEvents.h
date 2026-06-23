#pragma once

#include "Components/ActorComponent.h"
#include "FastDisTypes.h"
#include "FastDisPduEvents.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FFastDisPduEventSignature, const FFastDisPduEvent&, Event);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FFastDisRemoveEntityEventSignature, const FFastDisRemoveEntityEvent&, Event);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FFastDisEntityStateUpdateEventSignature, const FFastDisEntityStateUpdateEvent&, Event);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FFastDisFireEventSignature, const FFastDisFireEvent&, Event);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FFastDisDetonationEventSignature, const FFastDisDetonationEvent&, Event);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FFastDisStartResumeEventSignature, const FFastDisStartResumeEvent&, Event);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FFastDisStopFreezeEventSignature, const FFastDisStopFreezeEvent&, Event);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FFastDisEmissionEventSignature, const FFastDisEmissionEvent&, Event);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FFastDisSignalEventSignature, const FFastDisSignalEvent&, Event);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FFastDisDesignatorEventSignature, const FFastDisDesignatorEvent&, Event);

UCLASS(ClassGroup = (FastDIS), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class FASTDISUNREAL_API UFastDisPduEventComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UFastDisPduEventComponent();

    UFUNCTION(BlueprintCallable, Category = "FastDIS|PDU")
    bool EmitPduEvent(const TArray<uint8>& Packet, const FString& SourceEndpoint = TEXT(""));

    UFUNCTION(BlueprintCallable, Category = "FastDIS|PDU")
    static bool ParsePduHeader(const TArray<uint8>& Packet, FFastDisPduHeader& OutHeader);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|PDU")
    static bool ParseRemoveEntityEvent(const FFastDisPduEvent& Event, FFastDisRemoveEntityEvent& OutEvent);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|PDU")
    static bool ParseEntityStateUpdateEvent(const FFastDisPduEvent& Event, FFastDisEntityStateUpdateEvent& OutEvent);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|PDU")
    static bool ParseFireEvent(const FFastDisPduEvent& Event, FFastDisFireEvent& OutEvent);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|PDU")
    static bool ParseDetonationEvent(const FFastDisPduEvent& Event, FFastDisDetonationEvent& OutEvent);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|PDU")
    static bool ParseStartResumeEvent(const FFastDisPduEvent& Event, FFastDisStartResumeEvent& OutEvent);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|PDU")
    static bool ParseStopFreezeEvent(const FFastDisPduEvent& Event, FFastDisStopFreezeEvent& OutEvent);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|PDU")
    static bool ParseEmissionEvent(const FFastDisPduEvent& Event, FFastDisEmissionEvent& OutEvent);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|PDU")
    static bool ParseSignalEvent(const FFastDisPduEvent& Event, FFastDisSignalEvent& OutEvent);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|PDU")
    static bool ParseDesignatorEvent(const FFastDisPduEvent& Event, FFastDisDesignatorEvent& OutEvent);

    static bool ParsePduHeaderBytes(const uint8* Data, int32 Length, FFastDisPduHeader& OutHeader);
    void BroadcastPduEvent(const FFastDisPduEvent& Event);

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisPduEventSignature OnPduReceived;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisPduEventSignature OnEntityState;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisPduEventSignature OnEntityStateUpdate;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisEntityStateUpdateEventSignature OnEntityStateUpdateDecoded;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisPduEventSignature OnRemoveEntity;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisRemoveEntityEventSignature OnRemoveEntityDecoded;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisPduEventSignature OnFire;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisFireEventSignature OnFireDecoded;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisPduEventSignature OnDetonation;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisDetonationEventSignature OnDetonationDecoded;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisPduEventSignature OnStartResume;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisStartResumeEventSignature OnStartResumeDecoded;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisPduEventSignature OnStopFreeze;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisStopFreezeEventSignature OnStopFreezeDecoded;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisPduEventSignature OnEmission;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisEmissionEventSignature OnEmissionDecoded;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisPduEventSignature OnSignal;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisSignalEventSignature OnSignalDecoded;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisPduEventSignature OnDesignator;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisDesignatorEventSignature OnDesignatorDecoded;

    UPROPERTY(BlueprintAssignable, Category = "FastDIS|PDU")
    FFastDisPduEventSignature OnMalformedPdu;
};
