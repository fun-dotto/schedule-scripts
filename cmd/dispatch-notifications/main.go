package main

import (
	"context"
	"flag"
	"log"

	firebase "firebase.google.com/go/v4"
	"github.com/fun-dotto/schedule-scripts/internal/database"
	"github.com/fun-dotto/schedule-scripts/internal/repository"
	"github.com/fun-dotto/schedule-scripts/internal/service"
	"github.com/joho/godotenv"
)

func main() {
	dryRun := flag.Bool("dry-run", false, "If set, log planned FCM sends without actually calling Firebase or updating notified_at")
	flag.Parse()

	if err := godotenv.Load(); err != nil {
		log.Printf("Warning: .env file not found: %v", err)
	}

	db, err := database.ConnectWithConnectorIAMAuthN()
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer func() {
		if err := database.Close(db); err != nil {
			log.Printf("Failed to close database: %v", err)
		}
	}()

	ctx := context.Background()

	firebaseApp, err := firebase.NewApp(ctx, nil)
	if err != nil {
		log.Fatalf("Failed to initialize Firebase app: %v", err)
	}
	messagingClient, err := firebaseApp.Messaging(ctx)
	if err != nil {
		log.Fatalf("Failed to initialize Firebase Messaging client: %v", err)
	}

	notificationRepo := repository.NewNotificationRepository(db)
	fcmTokenRepo := repository.NewFCMTokenRepository(db)

	svc := service.NewNotificationDispatchService(notificationRepo, fcmTokenRepo, messagingClient)

	summary, err := svc.DispatchNotifications(ctx, *dryRun)
	if err != nil {
		log.Fatalf("Failed to dispatch notifications: %v", err)
	}
	log.Printf(
		"dispatch summary: dry_run=%t pending=%d dispatched=%d no_token_skip=%d failed_send=%d total_fcm_sent=%d",
		summary.DryRun,
		summary.Pending,
		summary.Dispatched,
		summary.NoTokenSkip,
		summary.FailedSend,
		summary.TotalFCMSent,
	)
}
