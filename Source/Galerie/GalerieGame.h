#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "GalerieGame.generated.h"

class UCameraComponent;
class USpotLightComponent;
class UPointLightComponent;
class UStaticMeshComponent;
class UAudioComponent;
class USoundBase;
class ULightComponent;

/** Hrac: pohled z prvni osoby, baterka, kroky po mramoru. Vstup se cte primo z klaves (zadne mapovani). */
UCLASS()
class AGPCharacter : public ACharacter
{
	GENERATED_BODY()
public:
	AGPCharacter();
	virtual void BeginPlay() override;
	virtual void Tick(float Dt) override;

	UPROPERTY(VisibleAnywhere) TObjectPtr<UCameraComponent> Cam;
	UPROPERTY(VisibleAnywhere) TObjectPtr<USpotLightComponent> Torch;
	UPROPERTY() TArray<TObjectPtr<USoundBase>> Steps;
	bool bFrozen = false;
	float StepAcc = 0.f;
	float BobT = 0.f;
	int32 LastStep = -1;
};

/** Svetlo k sebrani: zarici koule, bodove svetlo a 3D zvuk. */
UCLASS()
class AGPOrb : public AActor
{
	GENERATED_BODY()
public:
	AGPOrb();
	virtual void BeginPlay() override;
	virtual void Tick(float Dt) override;

	UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Mesh;
	UPROPERTY(VisibleAnywhere) TObjectPtr<UPointLightComponent> Light;
	UPROPERTY(VisibleAnywhere) TObjectPtr<UAudioComponent> Hum;
	FVector Base = FVector::ZeroVector;
	float Phase = 0.f;
};

UCLASS()
class AGPGameMode : public AGameModeBase
{
	GENERATED_BODY()
public:
	AGPGameMode();
	virtual void BeginPlay() override;
	virtual void Tick(float Dt) override;

	UPROPERTY() TArray<TObjectPtr<AGPOrb>> Orbs;
	UPROPERTY() TArray<TObjectPtr<ULightComponent>> Flashes;
	UPROPERTY() TObjectPtr<USoundBase> SndPickup;
	UPROPERTY() TObjectPtr<USoundBase> SndWin;
	UPROPERTY() TObjectPtr<USoundBase> SndLose;
	UPROPERTY() TObjectPtr<USoundBase> SndTick;
	UPROPERTY() TArray<TObjectPtr<USoundBase>> SndThunder;

	int32 Total = 0;
	int32 Got = 0;
	float TimeLeft = 150.f;
	float Elapsed = 0.f;
	int32 State = 0;          // 0 hra, 1 vyhra, 2 prohra
	float NextThunder = 9.f;
	float FlashT = -1.f;
	float ThunderDelay = -1.f;
	float TickAcc = 0.f;
	float PickupFlash = 0.f;
};

UCLASS()
class AGPHUD : public AHUD
{
	GENERATED_BODY()
public:
	virtual void DrawHUD() override;
	void Centered(const FString& S, float Y, float Scale, FLinearColor C);
};
