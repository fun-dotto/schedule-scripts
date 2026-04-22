package main

import (
	"context"
	"log"

	"github.com/fun-dotto/schedule-scripts/internal/database"
	"github.com/fun-dotto/schedule-scripts/internal/repository"
	"github.com/fun-dotto/schedule-scripts/internal/service"
	"github.com/joho/godotenv"
)

func main() {
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

	cancelledRepo := repository.NewCancelledClassRepository(db)
	makeupRepo := repository.NewMakeupClassRepository(db)
	roomChangeRepo := repository.NewRoomChangeRepository(db)
	courseRegRepo := repository.NewCourseRegistrationRepository(db)
	notificationRepo := repository.NewNotificationRepository(db)

	svc := service.NewClassChangeNotificationService(
		cancelledRepo,
		makeupRepo,
		roomChangeRepo,
		courseRegRepo,
		notificationRepo,
	)

	summary, err := svc.EnqueueNotifications(context.Background())
	if err != nil {
		log.Fatalf("Failed to enqueue notifications: %v", err)
	}
	log.Printf(
		"enqueue summary: cancelled=%d makeup=%d room_change=%d skipped=%d",
		summary.CancelledEnqueued,
		summary.MakeupEnqueued,
		summary.RoomChangeEnqueued,
		summary.Skipped,
	)
}
