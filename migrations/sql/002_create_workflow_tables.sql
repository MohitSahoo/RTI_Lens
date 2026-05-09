-- Migration: Create workflow_sessions and workflow_actions tables
-- Description: Add tables for tracking RTI workflow sessions with Backboard.io integration
-- Date: 2024-05-08

-- Create workflow_sessions table
CREATE TABLE IF NOT EXISTS workflow_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    thread_id VARCHAR(255),

    -- Workflow metadata
    workflow_type VARCHAR(50) NOT NULL,
    workflow_stage VARCHAR(50) NOT NULL DEFAULT 'initiated',

    -- User context
    user_id VARCHAR(255),
    user_ip VARCHAR(50),

    -- Session state
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    session_metadata JSONB,

    -- History tracking
    retrieval_history JSONB,
    generation_history JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for workflow_sessions
CREATE INDEX IF NOT EXISTS idx_workflow_sessions_session_id ON workflow_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_workflow_sessions_thread_id ON workflow_sessions(thread_id);
CREATE INDEX IF NOT EXISTS idx_workflow_sessions_user_id ON workflow_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_sessions_created_at ON workflow_sessions(created_at DESC);

-- Create workflow_actions table
CREATE TABLE IF NOT EXISTS workflow_actions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,

    -- Action details
    action_type VARCHAR(50) NOT NULL,
    action_name VARCHAR(100) NOT NULL,

    -- Action data
    input_data JSONB,
    output_data JSONB,

    -- Metadata
    duration_ms INTEGER,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for workflow_actions
CREATE INDEX IF NOT EXISTS idx_workflow_actions_session_id ON workflow_actions(session_id);
CREATE INDEX IF NOT EXISTS idx_workflow_actions_action_type ON workflow_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_workflow_actions_created_at ON workflow_actions(created_at DESC);

-- Add comments
COMMENT ON TABLE workflow_sessions IS 'Tracks RTI workflow sessions with Backboard.io integration';
COMMENT ON TABLE workflow_actions IS 'Logs individual actions within workflow sessions';
COMMENT ON COLUMN workflow_sessions.thread_id IS 'Backboard.io thread identifier for session continuity';
COMMENT ON COLUMN workflow_sessions.workflow_type IS 'Type of workflow: rti_qa, rti_draft, appeal';
COMMENT ON COLUMN workflow_sessions.workflow_stage IS 'Current stage: initiated, drafting, review, appeal, completed';
