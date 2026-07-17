-- In-app notification records and employee-invitation lifecycle.

BEGIN;

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    read_at TIMESTAMPTZ,
    delivery_state VARCHAR(20) NOT NULL DEFAULT 'sent' CHECK (delivery_state IN ('sent', 'failed')),
    delivery_error TEXT,
    audit_event_id UUID REFERENCES audit_events(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_recipient_read ON notifications(recipient_id, read_at);
CREATE INDEX IF NOT EXISTS idx_notifications_recipient_created ON notifications(recipient_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_event_type ON notifications(event_type);

ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
REVOKE ALL PRIVILEGES ON TABLE notifications FROM anon, authenticated;

COMMENT ON TABLE notifications IS 'Per-employee in-app notification records for invitations, role changes, and account status events';

COMMIT;
