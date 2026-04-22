package database

import (
	"context"
	"database/sql"
	"fmt"
	"net"
	"os"
	"time"

	"cloud.google.com/go/cloudsqlconn"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/stdlib"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// ConnectWithConnectorIAMAuthN は単一プロセス内で1回呼ばれる前提。
// Dialer は Close() 経由で解放するためパッケージレベルで保持する。
var activeDialer *cloudsqlconn.Dialer

func ConnectWithConnectorIAMAuthN() (*gorm.DB, error) {
	getenv := func(k string) (string, error) {
		v := os.Getenv(k)
		if v == "" {
			return "", fmt.Errorf("%s environment variable not set", k)
		}
		return v, nil
	}

	dbUser, err := getenv("DB_IAM_USER") // e.g. 'service-account-name@project-id.iam'
	if err != nil {
		return nil, err
	}
	dbName, err := getenv("DB_NAME") // e.g. 'my-database'
	if err != nil {
		return nil, err
	}
	instanceConnectionName, err := getenv("INSTANCE_CONNECTION_NAME") // e.g. 'project:region:instance'
	if err != nil {
		return nil, err
	}

	d, err := cloudsqlconn.NewDialer(
		context.Background(),
		cloudsqlconn.WithIAMAuthN(),
		cloudsqlconn.WithLazyRefresh(),
	)
	if err != nil {
		return nil, fmt.Errorf("cloudsqlconn.NewDialer: %w", err)
	}
	success := false
	defer func() {
		if !success {
			_ = d.Close()
		}
	}()

	dsn := fmt.Sprintf("user=%s database=%s", dbUser, dbName)
	config, err := pgx.ParseConfig(dsn)
	if err != nil {
		return nil, err
	}

	config.DialFunc = func(ctx context.Context, network, instance string) (net.Conn, error) {
		return d.Dial(ctx, instanceConnectionName)
	}
	dbURI := stdlib.RegisterConnConfig(config)
	sqlDB, err := sql.Open("pgx", dbURI)
	if err != nil {
		return nil, fmt.Errorf("sql.Open: %w", err)
	}

	sqlDB.SetMaxOpenConns(20)
	sqlDB.SetMaxIdleConns(10)
	sqlDB.SetConnMaxLifetime(30 * time.Minute)
	sqlDB.SetConnMaxIdleTime(5 * time.Minute)

	db, err := gorm.Open(postgres.New(postgres.Config{
		Conn: sqlDB,
	}), &gorm.Config{})
	if err != nil {
		sqlDB.Close()
		return nil, fmt.Errorf("gorm.Open: %w", err)
	}

	activeDialer = d
	success = true
	return db, nil
}

func Close(db *gorm.DB) error {
	if db == nil {
		return nil
	}

	sqlDB, err := db.DB()
	if err != nil {
		return fmt.Errorf("failed to get database instance: %w", err)
	}

	var firstErr error
	if err := sqlDB.Close(); err != nil {
		firstErr = fmt.Errorf("failed to close database: %w", err)
	}

	if activeDialer != nil {
		if err := activeDialer.Close(); err != nil && firstErr == nil {
			firstErr = fmt.Errorf("failed to close dialer: %w", err)
		}
		activeDialer = nil
	}

	return firstErr
}
