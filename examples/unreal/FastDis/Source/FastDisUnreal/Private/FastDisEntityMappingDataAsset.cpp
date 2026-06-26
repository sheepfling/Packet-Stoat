#include "FastDisEntityMappingDataAsset.h"

#include "GameFramework/Actor.h"

namespace
{
TSubclassOf<AActor> ResolveConfiguredActorClass(const FFastDisEntityMappingRow& Row)
{
    if (Row.ActorClass)
    {
        return Row.ActorClass;
    }

    if (!Row.ActorClassSoftPath.IsNull())
    {
        if (UClass* LoadedClass = Row.ActorClassSoftPath.LoadSynchronous())
        {
            return LoadedClass;
        }
    }

    return nullptr;
}
}

bool UFastDisEntityMappingDataAsset::ResolveRow(const FFastDisEntityType& EntityType, FFastDisEntityMappingRow& OutRow) const
{
    int32 BestScore = -1;
    int32 BestPriority = TNumericLimits<int32>::Min();
    int32 BestRowIndex = -1;

    for (int32 RowIndex = 0; RowIndex < Rows.Num(); ++RowIndex)
    {
        const FFastDisEntityMappingRow& Row = Rows[RowIndex];
        TSubclassOf<AActor> ResolvedActorClass = ResolveConfiguredActorClass(Row);
        if (!ResolvedActorClass)
        {
            continue;
        }

        if (Row.EntityType.Matches(EntityType))
        {
            const int32 Score = Row.EntityType.Specificity();
            const int32 Priority = Row.Priority;
            const bool bBetterMatch = Score > BestScore ||
                                      (Score == BestScore && Priority > BestPriority) ||
                                      (Score == BestScore && Priority == BestPriority && (BestRowIndex < 0 || RowIndex < BestRowIndex));
            if (bBetterMatch)
            {
                BestScore = Score;
                BestPriority = Priority;
                BestRowIndex = RowIndex;
                OutRow = Row;
                OutRow.ActorClass = ResolvedActorClass;
            }
        }

        for (const FFastDisEntityType& AliasType : Row.AliasEntityTypes)
        {
            if (!AliasType.Matches(EntityType))
            {
                continue;
            }

            const int32 Score = AliasType.Specificity();
            const int32 Priority = Row.Priority;
            const bool bBetterMatch = Score > BestScore ||
                                      (Score == BestScore && Priority > BestPriority) ||
                                      (Score == BestScore && Priority == BestPriority && (BestRowIndex < 0 || RowIndex < BestRowIndex));
            if (bBetterMatch)
            {
                BestScore = Score;
                BestPriority = Priority;
                BestRowIndex = RowIndex;
                OutRow = Row;
                OutRow.ActorClass = ResolvedActorClass;
            }
        }
    }

    return BestRowIndex >= 0;
}

TSubclassOf<AActor> UFastDisEntityMappingDataAsset::ResolveActorClass(const FFastDisEntityType& EntityType, TSubclassOf<AActor> FallbackClass) const
{
    FFastDisEntityMappingRow ResolvedRow;
    if (ResolveRow(EntityType, ResolvedRow) && ResolvedRow.ActorClass)
    {
        return ResolvedRow.ActorClass;
    }

    return FallbackClass;
}
