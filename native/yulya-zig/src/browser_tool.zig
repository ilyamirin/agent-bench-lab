const std = @import("std");
const Io = std.Io;
const command_tools = @import("command_tools.zig");

pub fn runScenario(
    allocator: std.mem.Allocator,
    io: Io,
    repo_root: []const u8,
    scenario: []const u8,
    workspace: []const u8,
    run_root: []const u8,
    web_port: []const u8,
) !command_tools.CommandResult {
    return command_tools.run(allocator, io, repo_root, &.{
        "python3",
        "-m",
        "benchmark_lab.browser_scenarios",
        "--scenario",
        scenario,
        "--workspace",
        workspace,
        "--run-root",
        run_root,
        "--web-port",
        web_port,
    });
}
