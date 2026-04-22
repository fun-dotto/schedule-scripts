package repository

import (
	"context"
	"time"

	"github.com/fun-dotto/schedule-scripts/internal/database"
	"github.com/fun-dotto/schedule-scripts/internal/domain"
)

func (r *CancelledClassRepository) ListUpcoming(ctx context.Context, after time.Time) ([]domain.CancelledClass, error) {
	var rows []database.CancelledClass
	if err := r.db.WithContext(ctx).
		Preload("Subject").
		Where("date > ?", after).
		Find(&rows).Error; err != nil {
		return nil, err
	}
	out := make([]domain.CancelledClass, 0, len(rows))
	for i := range rows {
		out = append(out, rows[i].ToDomain())
	}
	return out, nil
}
