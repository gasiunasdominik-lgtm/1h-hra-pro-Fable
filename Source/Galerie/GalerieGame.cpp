#include "GalerieGame.h"
#include "Camera/CameraComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/AudioComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/LightComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Engine/StaticMesh.h"
#include "Engine/TargetPoint.h"
#include "Engine/Light.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Materials/MaterialInterface.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundWave.h"
#include "Sound/SoundAttenuation.h"
#include "UObject/ConstructorHelpers.h"
#include "InputCoreTypes.h"
#include "UnrealClient.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"

namespace
{
	USoundBase* LoadSnd(const TCHAR* Name, bool bLoop = false)
	{
		const FString Path = FString::Printf(TEXT("/Game/Audio/%s.%s"), Name, Name);
		USoundBase* S = LoadObject<USoundBase>(nullptr, *Path);
		if (bLoop)
		{
			if (USoundWave* W = Cast<USoundWave>(S)) { W->bLooping = true; }
		}
		return S;
	}
}

// ------------------------------------------------------------------ hrac

AGPCharacter::AGPCharacter()
{
	PrimaryActorTick.bCanEverTick = true;
	GetCapsuleComponent()->InitCapsuleSize(34.f, 88.f);

	Cam = CreateDefaultSubobject<UCameraComponent>(TEXT("Cam"));
	Cam->SetupAttachment(GetCapsuleComponent());
	Cam->SetRelativeLocation(FVector(0.f, 0.f, 68.f));
	Cam->bUsePawnControlRotation = true;
	Cam->SetFieldOfView(82.f);

	Torch = CreateDefaultSubobject<USpotLightComponent>(TEXT("Torch"));
	Torch->SetupAttachment(Cam);
	Torch->SetRelativeLocation(FVector(10.f, 14.f, -12.f));
	Torch->SetMobility(EComponentMobility::Movable);
	Torch->SetIntensityUnits(ELightUnits::Unitless);
	Torch->SetIntensity(5500.f);
	Torch->SetLightColor(FLinearColor(1.f, 0.93f, 0.82f));
	Torch->SetAttenuationRadius(1500.f);
	Torch->SetInnerConeAngle(9.f);
	Torch->SetOuterConeAngle(28.f);
	Torch->SetCastShadows(false);

	UCharacterMovementComponent* Mv = GetCharacterMovement();
	Mv->MaxWalkSpeed = 250.f;
	Mv->BrakingDecelerationWalking = 1400.f;
	Mv->MaxAcceleration = 1400.f;
	Mv->JumpZVelocity = 330.f;
	Mv->AirControl = 0.2f;
	bUseControllerRotationYaw = true;
}

void AGPCharacter::BeginPlay()
{
	Super::BeginPlay();
	for (int32 i = 1; i <= 6; ++i)
	{
		if (USoundBase* S = LoadSnd(*FString::Printf(TEXT("step_%d"), i))) { Steps.Add(S); }
	}
	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		PC->SetInputMode(FInputModeGameOnly());
		PC->bShowMouseCursor = false;
	}
}

void AGPCharacter::Tick(float Dt)
{
	Super::Tick(Dt);
	APlayerController* PC = Cast<APlayerController>(GetController());
	if (!PC) { return; }

	// rozhlizeni
	float Mx = 0.f, My = 0.f;
	PC->GetInputMouseDelta(Mx, My);
	FRotator R = PC->GetControlRotation();
	R.Yaw += Mx * 0.11f;
	R.Pitch = FMath::Clamp(FRotator::NormalizeAxis(R.Pitch) + My * 0.11f, -82.f, 82.f);
	R.Roll = 0.f;
	PC->SetControlRotation(R);

	// chuze
	float F = 0.f, S = 0.f;
	if (!bFrozen)
	{
		F = (PC->IsInputKeyDown(EKeys::W) || PC->IsInputKeyDown(EKeys::Up) ? 1.f : 0.f) - (PC->IsInputKeyDown(EKeys::S) || PC->IsInputKeyDown(EKeys::Down) ? 1.f : 0.f);
		S = (PC->IsInputKeyDown(EKeys::D) || PC->IsInputKeyDown(EKeys::Right) ? 1.f : 0.f) - (PC->IsInputKeyDown(EKeys::A) || PC->IsInputKeyDown(EKeys::Left) ? 1.f : 0.f);
		if (PC->WasInputKeyJustPressed(EKeys::SpaceBar)) { Jump(); }
		if (PC->WasInputKeyJustPressed(EKeys::F)) { Torch->SetVisibility(!Torch->IsVisible()); }
	}
	const bool bRun = PC->IsInputKeyDown(EKeys::LeftShift);
	GetCharacterMovement()->MaxWalkSpeed = bRun ? 470.f : 250.f;
	const FRotator YawRot(0.f, R.Yaw, 0.f);
	const FRotationMatrix M(YawRot);
	AddMovementInput(M.GetUnitAxis(EAxis::X), F);
	AddMovementInput(M.GetUnitAxis(EAxis::Y), S);

	// kroky + pohup hlavy
	const float Speed = GetVelocity().Size2D();
	const bool bGround = GetCharacterMovement()->IsMovingOnGround();
	if (bGround && Speed > 30.f)
	{
		const float Stride = bRun ? 185.f : 150.f;
		StepAcc += Speed * Dt;
		BobT += Speed * Dt / Stride * PI;
		if (StepAcc >= Stride)
		{
			StepAcc = 0.f;
			if (Steps.Num() > 0)
			{
				int32 i = FMath::RandRange(0, Steps.Num() - 1);
				if (i == LastStep) { i = (i + 1) % Steps.Num(); }
				LastStep = i;
				UGameplayStatics::PlaySound2D(this, Steps[i], bRun ? 1.0f : 0.72f, FMath::FRandRange(0.93f, 1.07f));
			}
		}
	}
	else
	{
		StepAcc = FMath::Min(StepAcc, 90.f);
	}
	const float Amp = FMath::Clamp(Speed / 250.f, 0.f, 1.6f);
	Cam->SetRelativeLocation(FVector(0.f, FMath::Cos(BobT) * 0.9f * Amp, 68.f + FMath::Abs(FMath::Sin(BobT)) * 2.2f * Amp));
}

// ------------------------------------------------------------------ svetlo

AGPOrb::AGPOrb()
{
	PrimaryActorTick.bCanEverTick = true;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	Mesh->SetupAttachment(RootComponent);
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (Sphere.Succeeded()) { Mesh->SetStaticMesh(Sphere.Object); }
	Mesh->SetRelativeScale3D(FVector(0.2f));
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetCastShadow(false);
	Mesh->SetMobility(EComponentMobility::Movable);

	Light = CreateDefaultSubobject<UPointLightComponent>(TEXT("Light"));
	Light->SetupAttachment(RootComponent);
	Light->SetMobility(EComponentMobility::Movable);
	Light->SetIntensityUnits(ELightUnits::Unitless);
	Light->SetIntensity(4500.f);
	Light->SetLightColor(FLinearColor(1.f, 0.72f, 0.28f));
	Light->SetAttenuationRadius(520.f);
	Light->SetCastShadows(false);

	Hum = CreateDefaultSubobject<UAudioComponent>(TEXT("Hum"));
	Hum->SetupAttachment(RootComponent);
	Hum->bAutoActivate = false;
	Hum->bOverrideAttenuation = true;
	Hum->AttenuationOverrides.bAttenuate = true;
	Hum->AttenuationOverrides.bSpatialize = true;
	Hum->AttenuationOverrides.AttenuationShapeExtents = FVector(90.f);
	Hum->AttenuationOverrides.FalloffDistance = 1500.f;
}

void AGPOrb::BeginPlay()
{
	Super::BeginPlay();
	Base = GetActorLocation();
	Phase = FMath::FRandRange(0.f, 6.28f);
	if (UMaterialInterface* M = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Mat/M_Orb.M_Orb")))
	{
		Mesh->SetMaterial(0, M);
	}
	if (USoundBase* S = LoadSnd(TEXT("orb_hum"), true))
	{
		Hum->SetSound(S);
		Hum->SetVolumeMultiplier(0.45f);
		Hum->SetPitchMultiplier(FMath::FRandRange(0.94f, 1.06f));
		Hum->Play(FMath::FRandRange(0.f, 5.f));
	}
}

void AGPOrb::Tick(float Dt)
{
	Super::Tick(Dt);
	Phase += Dt;
	SetActorLocation(Base + FVector(0.f, 0.f, FMath::Sin(Phase * 1.3f) * 9.f));
	Light->SetIntensity(4500.f * (0.82f + 0.18f * FMath::Sin(Phase * 3.1f) * FMath::Sin(Phase * 0.7f)));
}

// ------------------------------------------------------------------ pravidla

AGPGameMode::AGPGameMode()
{
	PrimaryActorTick.bCanEverTick = true;
	DefaultPawnClass = AGPCharacter::StaticClass();
	HUDClass = AGPHUD::StaticClass();
}

void AGPGameMode::BeginPlay()
{
	Super::BeginPlay();
	UWorld* W = GetWorld();

	// svetla vznikaji na znackach (TargetPoint), ktere do mapy rozmistil Tools/build_level.py
	TArray<FVector> Spots;
	for (TActorIterator<ATargetPoint> It(W); It; ++It) { Spots.Add(It->GetActorLocation()); }
	if (Spots.Num() == 0)
	{
		for (int32 i = 0; i < 8; ++i) { Spots.Add(FVector(-1200.f + i * 350.f, (i % 2) ? 450.f : -450.f, 130.f)); }
	}
	for (const FVector& P : Spots)
	{
		if (AGPOrb* O = W->SpawnActor<AGPOrb>(AGPOrb::StaticClass(), P, FRotator::ZeroRotator)) { Orbs.Add(O); }
	}
	Total = Orbs.Num();
	TimeLeft = 60.f + 14.f * Total;

	// blesky: pohybliva svetla za okny oznacena tagem "Lightning"
	for (TActorIterator<ALight> It(W); It; ++It)
	{
		if (It->ActorHasTag(TEXT("Lightning")) && It->GetLightComponent())
		{
			It->GetLightComponent()->SetIntensity(0.f);
			Flashes.Add(It->GetLightComponent());
		}
	}

	if (FParse::Param(FCommandLine::Get(), TEXT("shots")))
	{
		ShotIdx = -1;
		FParse::Value(FCommandLine::Get(), TEXT("shotwarm="), ShotWarm);
	}

	SndPickup = LoadSnd(TEXT("pickup"));
	SndWin = LoadSnd(TEXT("win"));
	SndLose = LoadSnd(TEXT("lose"));
	SndTick = LoadSnd(TEXT("tick"));
	if (USoundBase* T1 = LoadSnd(TEXT("thunder_1"))) { SndThunder.Add(T1); }
	if (USoundBase* T2 = LoadSnd(TEXT("thunder_2"))) { SndThunder.Add(T2); }
	if (USoundBase* Rain = LoadSnd(TEXT("amb_rain"), true)) { UGameplayStatics::SpawnSound2D(this, Rain, 0.9f); }
}

void AGPGameMode::Tick(float Dt)
{
	Super::Tick(Dt);
	Elapsed += Dt;
	PickupFlash = FMath::Max(0.f, PickupFlash - Dt);
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	AGPCharacter* Ch = PC ? Cast<AGPCharacter>(PC->GetPawn()) : nullptr;

	// bourka: zablesk za okny, hrom dorazi se zpozdenim
	NextThunder -= Dt;
	if (NextThunder <= 0.f)
	{
		NextThunder = FMath::FRandRange(22.f, 42.f);
		FlashT = 0.f;
		ThunderDelay = FMath::FRandRange(0.5f, 1.6f);
	}
	if (FlashT >= 0.f)
	{
		FlashT += Dt;
		const float A = (FlashT < 0.09f) ? 1.f : (FlashT < 0.17f) ? 0.1f : (FlashT < 0.30f) ? 0.8f : FMath::Max(0.f, 0.8f - (FlashT - 0.30f) * 2.6f);
		for (ULightComponent* L : Flashes) { if (L) { L->SetIntensity(A * 1500000.f); } }
		if (FlashT > 0.7f)
		{
			FlashT = -1.f;
			for (ULightComponent* L : Flashes) { if (L) { L->SetIntensity(0.f); } }
		}
	}
	if (ThunderDelay >= 0.f)
	{
		ThunderDelay -= Dt;
		if (ThunderDelay < 0.f && SndThunder.Num() > 0)
		{
			UGameplayStatics::PlaySound2D(this, SndThunder[FMath::RandRange(0, SndThunder.Num() - 1)], FMath::FRandRange(0.7f, 1.f), FMath::FRandRange(0.9f, 1.05f));
		}
	}

	// overovaci rezim: -shots => hra sama vyfoti nekolik pohledu do Saved/Shots a skonci
	if (ShotIdx > -2 && Ch && PC)
	{
		static const float Views[][5] = {
			{-1620.f, 0.f, 0.f, -4.f, 0.f}, {-1100.f, -150.f, -62.f, -6.f, 0.f}, {-250.f, 120.f, -105.f, -3.f, 0.f},
			{200.f, -200.f, 62.f, 2.f, 0.f}, {1500.f, 150.f, 172.f, -12.f, 0.f}, {1150.f, -330.f, -60.f, 4.f, 1.f} };
		const int32 N = UE_ARRAY_COUNT(Views);
		ShotT += Dt;
		if (ShotIdx == -1 && ShotT > ShotWarm) { ShotIdx = 0; ShotT = 0.f; bShotTaken = false; }
		if (ShotIdx >= 0 && ShotIdx < N)
		{
			const float* Vw = Views[ShotIdx];
			Ch->bFrozen = true;
			Ch->SetActorLocation(FVector(Vw[0], Vw[1], 98.f));
			PC->SetControlRotation(FRotator(Vw[3], Vw[2], 0.f));
			Ch->Torch->SetVisibility(Vw[4] > 0.5f);
			if (!bShotTaken && ShotT > 2.5f)
			{
				bShotTaken = true;
				FScreenshotRequest::RequestScreenshot(FPaths::ProjectSavedDir() / FString::Printf(TEXT("Shots/view_%d.png"), ShotIdx), true, false);
			}
			// mereni vykonu: prumerne FPS behem pohledu (po ustaleni)
			static float FpsAcc = 0.f; static int32 FpsN = 0;
			if (ShotT > 1.f) { FpsAcc += Dt; ++FpsN; }
			if (ShotT > 3.5f)
			{
				UE_LOG(LogTemp, Display, TEXT("GALERIE FPS view %d: %.1f"), ShotIdx, FpsN > 0 ? FpsN / FMath::Max(FpsAcc, 0.001f) : 0.f);
				FpsAcc = 0.f; FpsN = 0;
				++ShotIdx; ShotT = 0.f; bShotTaken = false;
			}
		}
		else if (ShotIdx >= N)
		{
			UKismetSystemLibrary::QuitGame(this, PC, EQuitPreference::Quit, false);
			return;
		}
		TimeLeft = FMath::Max(TimeLeft, 100.f);
	}

	if (PC)
	{
		if (PC->WasInputKeyJustPressed(EKeys::R))
		{
			UGameplayStatics::OpenLevel(this, FName(*UGameplayStatics::GetCurrentLevelName(this)));
			return;
		}
		if (PC->WasInputKeyJustPressed(EKeys::Escape))
		{
			UKismetSystemLibrary::QuitGame(this, PC, EQuitPreference::Quit, false);
			return;
		}
	}
	if (State != 0 || !Ch) { return; }

	TimeLeft -= Dt;
	if (TimeLeft < 20.f)
	{
		TickAcc += Dt;
		if (TickAcc >= 1.f) { TickAcc = 0.f; if (SndTick) { UGameplayStatics::PlaySound2D(this, SndTick, 0.8f); } }
	}

	const FVector P = Ch->GetActorLocation();
	for (int32 i = Orbs.Num() - 1; i >= 0; --i)
	{
		AGPOrb* O = Orbs[i];
		if (!O) { Orbs.RemoveAt(i); continue; }
		if (FVector::Dist(P, O->GetActorLocation()) < 150.f)
		{
			O->Destroy();
			Orbs.RemoveAt(i);
			++Got;
			PickupFlash = 1.f;
			if (SndPickup) { UGameplayStatics::PlaySound2D(this, SndPickup, 0.9f, 1.f + 0.03f * Got); }
		}
	}

	if (Total > 0 && Got >= Total)
	{
		State = 1;
		if (SndWin) { UGameplayStatics::PlaySound2D(this, SndWin); }
	}
	else if (TimeLeft <= 0.f)
	{
		TimeLeft = 0.f;
		State = 2;
		Ch->bFrozen = true;
		if (SndLose) { UGameplayStatics::PlaySound2D(this, SndLose); }
	}
}

// ------------------------------------------------------------------ HUD

void AGPHUD::Centered(const FString& S, float Y, float Scale, FLinearColor C)
{
	UFont* Font = GEngine ? GEngine->GetLargeFont() : nullptr;
	float Tw = 0.f, Th = 0.f;
	GetTextSize(S, Tw, Th, Font, Scale);
	const float X = (Canvas->ClipX - Tw) * 0.5f;
	DrawText(S, FLinearColor(0.f, 0.f, 0.f, C.A * 0.7f), X + 2.f, Y + 2.f, Font, Scale, false);
	DrawText(S, C, X, Y, Font, Scale, false);
}

void AGPHUD::DrawHUD()
{
	Super::DrawHUD();
	AGPGameMode* GM = GetWorld() ? GetWorld()->GetAuthGameMode<AGPGameMode>() : nullptr;
	if (!GM || !Canvas) { return; }
	const float W = Canvas->ClipX, H = Canvas->ClipY;
	const float K = H / 1080.f;
	const FLinearColor Gold(1.f, 0.82f, 0.45f, 1.f);
	const FLinearColor White(0.95f, 0.95f, 0.92f, 1.f);

	// zamerovaci tecka
	DrawRect(FLinearColor(1.f, 1.f, 1.f, 0.55f), W * 0.5f - 1.5f, H * 0.5f - 1.5f, 3.f, 3.f);

	// zlaty zablesk pri sebrani
	if (GM->PickupFlash > 0.f)
	{
		DrawRect(FLinearColor(1.f, 0.75f, 0.3f, 0.16f * GM->PickupFlash), 0.f, 0.f, W, H);
	}

	const int32 T = FMath::CeilToInt(GM->TimeLeft);
	const bool bLow = GM->TimeLeft < 20.f && GM->State == 0;
	Centered(FString::Printf(TEXT("%d : %02d"), T / 60, T % 60), 34.f * K, 2.6f * K, bLow ? FLinearColor(1.f, 0.3f, 0.2f, 1.f) : White);
	Centered(FString::Printf(TEXT("SVĚTLA  %d / %d"), GM->Got, GM->Total), 96.f * K, 1.5f * K, Gold);

	if (GM->State == 0 && GM->Elapsed < 9.f)
	{
		const float A = FMath::Clamp(FMath::Min(GM->Elapsed, 9.f - GM->Elapsed), 0.f, 1.f);
		FLinearColor C1 = Gold; C1.A = A;
		FLinearColor C2 = White; C2.A = A;
		Centered(TEXT("GALERIE O PŮLNOCI"), H * 0.30f, 4.2f * K, C1);
		Centered(TEXT("Posbírej všechna světla, než se galerie zamkne. Poslouchej - každé světlo zpívá."), H * 0.30f + 110.f * K, 1.5f * K, C2);
		Centered(TEXT("WASD chůze   ·   myš rozhled   ·   Shift běh   ·   F baterka   ·   R znovu   ·   Esc konec"), H * 0.30f + 160.f * K, 1.2f * K, C2);
	}
	if (GM->State == 1)
	{
		DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.45f), 0.f, H * 0.36f, W, 230.f * K);
		Centered(TEXT("VŠECHNA SVĚTLA JSOU TVÁ"), H * 0.40f, 3.8f * K, Gold);
		Centered(FString::Printf(TEXT("Zbývalo %d s.   R = hrát znovu"), T), H * 0.40f + 110.f * K, 1.6f * K, White);
	}
	else if (GM->State == 2)
	{
		DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.6f), 0.f, H * 0.36f, W, 230.f * K);
		Centered(TEXT("GALERIE SE ZAMKLA"), H * 0.40f, 3.8f * K, FLinearColor(1.f, 0.35f, 0.25f, 1.f));
		Centered(FString::Printf(TEXT("Sebráno %d z %d.   R = zkusit znovu"), GM->Got, GM->Total), H * 0.40f + 110.f * K, 1.6f * K, White);
	}
}
