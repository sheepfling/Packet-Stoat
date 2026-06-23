#pragma once

#include "Blueprint/UserWidget.h"
#include "FastDisTypes.h"
#include "FastDisRuntimeStatusWidget.generated.h"

class AFastDisDemoController;
class UFastDisRuntimeMonitorComponent;

UCLASS(BlueprintType, Blueprintable)
class FASTDISUNREAL_API UFastDisRuntimeStatusWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "FastDIS|Monitor")
    void BindDemoController(AFastDisDemoController* InDemoController);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Monitor")
    void BindRuntimeMonitor(UFastDisRuntimeMonitorComponent* InRuntimeMonitor);

    UFUNCTION(BlueprintCallable, Category = "FastDIS|Monitor")
    FFastDisRuntimeMonitorSnapshot RefreshSnapshot();

    UFUNCTION(BlueprintPure, Category = "FastDIS|Monitor")
    FFastDisRuntimeMonitorSnapshot GetLastSnapshot() const;

    UFUNCTION(BlueprintPure, Category = "FastDIS|Monitor")
    FText GetStatusText() const;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "FastDIS|Monitor")
    bool bAutoFindDemoController = true;

protected:
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
    void TryAutoBindDemoController();
    static FText FormatSnapshot(const FFastDisRuntimeMonitorSnapshot& Snapshot);

private:
    UPROPERTY(Transient)
    TObjectPtr<AFastDisDemoController> DemoController = nullptr;

    UPROPERTY(Transient)
    TObjectPtr<UFastDisRuntimeMonitorComponent> RuntimeMonitor = nullptr;

    FFastDisRuntimeMonitorSnapshot LastSnapshot;
};
