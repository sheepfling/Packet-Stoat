#include "FastDisGeoreferenceAdapterComponent.h"

#include "Engine/World.h"
#include "FastDisWorldSubsystem.h"
#include "UObject/UnrealType.h"

UFastDisGeoreferenceAdapterComponent::UFastDisGeoreferenceAdapterComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UFastDisGeoreferenceAdapterComponent::BeginPlay()
{
    Super::BeginPlay();
    if (!bApplyOnBeginPlay)
    {
        return;
    }

    if (GeoreferenceSource)
    {
        ApplyFromSourceObject();
    }
    else
    {
        ApplyManualGeoreference();
    }
}

bool UFastDisGeoreferenceAdapterComponent::ApplyManualGeoreference()
{
    return ApplyGeoreference(ManualGeoreference);
}

bool UFastDisGeoreferenceAdapterComponent::ApplyFromSourceObject()
{
    FFastDisGeoreference SourceGeoreference;
    if (!ReadSourceGeoreference(SourceGeoreference))
    {
        return false;
    }
    return ApplyGeoreference(SourceGeoreference);
}

bool UFastDisGeoreferenceAdapterComponent::ReadSourceGeoreference(FFastDisGeoreference& OutGeoreference) const
{
    if (!GeoreferenceSource)
    {
        return false;
    }

    double Latitude = 0.0;
    double Longitude = 0.0;
    double Height = 0.0;
    if (!ReadNumericProperty(GeoreferenceSource, LatitudePropertyName, Latitude) ||
        !ReadNumericProperty(GeoreferenceSource, LongitudePropertyName, Longitude) ||
        !ReadNumericProperty(GeoreferenceSource, HeightPropertyName, Height))
    {
        return false;
    }

    bool bApplyOrientation = ManualGeoreference.bApplyOrientation;
    ReadBoolProperty(GeoreferenceSource, ApplyOrientationPropertyName, bApplyOrientation);

    OutGeoreference.LatitudeDegrees = Latitude;
    OutGeoreference.LongitudeDegrees = Longitude;
    OutGeoreference.HeightMeters = Height;
    OutGeoreference.bApplyOrientation = bApplyOrientation;
    return true;
}

bool UFastDisGeoreferenceAdapterComponent::ApplyGeoreference(const FFastDisGeoreference& Georeference)
{
    UWorld* World = GetWorld();
    UFastDisWorldSubsystem* Subsystem = World ? World->GetSubsystem<UFastDisWorldSubsystem>() : nullptr;
    if (!Subsystem)
    {
        return false;
    }

    Subsystem->ConfigureGeoreference(Georeference);
    return true;
}

bool UFastDisGeoreferenceAdapterComponent::ReadNumericProperty(const UObject* Source, FName PropertyName, double& OutValue)
{
    if (!Source || PropertyName.IsNone())
    {
        return false;
    }

    const FProperty* Property = Source->GetClass()->FindPropertyByName(PropertyName);
    const FNumericProperty* NumericProperty = CastField<FNumericProperty>(Property);
    if (!NumericProperty)
    {
        return false;
    }

    const void* ValuePtr = NumericProperty->ContainerPtrToValuePtr<void>(Source);
    OutValue = NumericProperty->IsFloatingPoint()
        ? NumericProperty->GetFloatingPointPropertyValue(ValuePtr)
        : static_cast<double>(NumericProperty->GetSignedIntPropertyValue(ValuePtr));
    return true;
}

bool UFastDisGeoreferenceAdapterComponent::ReadBoolProperty(const UObject* Source, FName PropertyName, bool& OutValue)
{
    if (!Source || PropertyName.IsNone())
    {
        return false;
    }

    const FProperty* Property = Source->GetClass()->FindPropertyByName(PropertyName);
    const FBoolProperty* BoolProperty = CastField<FBoolProperty>(Property);
    if (!BoolProperty)
    {
        return false;
    }

    OutValue = BoolProperty->GetPropertyValue_InContainer(Source);
    return true;
}
