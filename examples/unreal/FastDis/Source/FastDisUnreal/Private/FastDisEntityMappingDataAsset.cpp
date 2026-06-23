#include "FastDisEntityMappingDataAsset.h"

#include "GameFramework/Actor.h"

TSubclassOf<AActor> UFastDisEntityMappingDataAsset::ResolveActorClass(const FFastDisEntityType& EntityType, TSubclassOf<AActor> FallbackClass) const
{
    TSubclassOf<AActor> BestClass = FallbackClass;
    int32 BestScore = -1;

    for (const FFastDisEntityMappingRow& Row : Rows)
    {
        if (!Row.ActorClass || !Row.EntityType.Matches(EntityType))
        {
            continue;
        }

        const int32 Score = Row.EntityType.Specificity();
        if (Score > BestScore)
        {
            BestClass = Row.ActorClass;
            BestScore = Score;
        }
    }

    return BestClass;
}
