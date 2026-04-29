const std = @import("std");

pub const Phase = enum {
    scan,
    implement,
    validate,
    repair,
    done,
};

pub const Iteration = struct {
    phase: Phase,
    analysis: []const u8,
    applied_changes: bool,
    validations_passed: bool,
};

pub const Summary = struct {
    agent_id: []const u8,
    provider: []const u8,
    model: []const u8,
    task_supported: bool,
    done_claim: bool,
    done_justification: []const u8,
    validations_passed: bool,
    failure_reason: ?[]const u8,
    iteration_count: usize,
};
